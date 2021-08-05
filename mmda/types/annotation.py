"""

Annotations are objects that are 'aware' of the Document

Collections of Annotations are how one constructs a new Iterable of Group-type objects within the Document

"""

from typing import List, Optional, Dict, Tuple, Type
from abc import abstractmethod
from dataclasses import dataclass, field


from mmda.types.span import Span
from mmda.types.box import Box, BoxGroup

from intervaltree import IntervalTree


@dataclass
class Annotation:
    """Annotation is intended for storing model predictions for a document."""

    doc: Optional["Document"] = field(default=False, init=False)
    # Specify an attribute with default value in the parent class
    # Ref: https://stackoverflow.com/a/58525728

    @abstractmethod
    def to_json(self) -> Dict:
        pass

    def attach_doc(self, doc: "Document") -> None:
        if not self.doc:
            self.doc = doc
        else:
            raise AttributeError(f'This annotation already has an attached document')

    # TODO[kylel] - comment explaining
    def __getattr__(self, field: str) -> List["Annotation"]:
        if field in self.doc.fields:
            return self.doc.find_overlapping(self, field)
        else:
            return self.__getattribute__(field)     # TODO[kylel] - alternatively, have it fail



@dataclass
class SpanGroup(Annotation):
    spans: List[Span] = field(default_factory=list)
    id: Optional[int] = None
    text: Optional[str] = None
    type: Optional[str] = None
    box_group: Optional[BoxGroup] = None

    def to_json(self) -> Dict:
        return dict(
            _type="SpanGroup",  # Used for differenting between DocSpan and DocBox when loading the json
            span_group=[span.to_json() for span in self.spans],
            text=self.text,
            type=self.type,
            box_group=self.box_group.to_json() if self.box_group else None,
        )

    def __getitem__(self, key: int):
        return self.spans[key]



@dataclass
class DocBoxGroup(Annotation):
    box_group: BoxGroup
    type: Optional[str] = None

    def to_json(self) -> Dict:
        return dict(
            _type="DocBoxGroup",  # Used for differenting between DocSpan and DocBox when loading the json
            box_group=self.box_group.to_json(),
            type=self.type
        )




# TODO[kylel] -- Implement
@dataclass
class Indexer:
    """Stores an index for a particular collection of Annotations.
    Indexes in this library focus on *INTERSECT* relations."""

    @abstractmethod
    def find(self, query: Annotation) -> List[Annotation]:
        """Returns all matching Annotations given a suitable query"""


@dataclass
class SpanGroupIndexer(Indexer):

    def __post_init__(self):
        self._index: IntervalTree = IntervalTree()

    # TODO[kylel] - maybe have more nullable args for different types of queryes (just start/end ints, just SpanGroup)
    def find(self, query: Annotation) -> List[Annotation]:
        if not isinstance(query, SpanGroup):
            raise ValueError(f'SpanGroupIndexer only works with `query` that is SpanGroup type')

        all_matched_span_groups = []
        for span in query.span_group:
            for matched_span_group in self._index[span.start : span.end]:
                if matched_span_group not in all_matched_span_groups: # Deduplicate
                    all_matched_span_groups.append(matched_span_group)
        return all_matched_span_groups
