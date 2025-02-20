"""

@kylel


"""

import logging

logger = logging.getLogger(__name__)

from mmda.parsers.pdfplumber_parser import PDFPlumberParser
from mmda.predictors.hf_predictors.token_classification_predictor import (
    IVILATokenClassificationPredictor,
)
from mmda.predictors.lp_predictors import LayoutParserPredictor
from mmda.predictors.sklearn_predictors.svm_word_predictor import SVMWordPredictor
from mmda.rasterizers.rasterizer import PDF2ImageRasterizer
from mmda.recipes.recipe import Recipe
from mmda.types import *


class CoreRecipe(Recipe):
    def __init__(
        self,
        effdet_publaynet_predictor_path: str = "lp://efficientdet/PubLayNet",
        effdet_mfd_predictor_path: str = "lp://efficientdet/MFD",
        vila_predictor_path: str = "allenai/ivila-row-layoutlm-finetuned-s2vl-v2",
        svm_word_predictor_path: str = "https://ai2-s2-research-public.s3.us-west-2.amazonaws.com/mmda/models/svm_word_predictor.tar.gz",
    ):
        logger.info("Instantiating recipe...")
        self.parser = PDFPlumberParser()
        self.rasterizer = PDF2ImageRasterizer()
        self.word_predictor = SVMWordPredictor.from_path(svm_word_predictor_path)
        self.effdet_publaynet_predictor = LayoutParserPredictor.from_pretrained(
            effdet_publaynet_predictor_path
        )
        self.effdet_mfd_predictor = LayoutParserPredictor.from_pretrained(
            effdet_mfd_predictor_path
        )
        self.vila_predictor = IVILATokenClassificationPredictor.from_pretrained(
            vila_predictor_path
        )
        logger.info("Finished instantiating recipe")

    def from_path(self, pdfpath: str) -> Document:
        logger.info("Parsing document...")
        doc = self.parser.parse(input_pdf_path=pdfpath)

        logger.info("Rasterizing document...")
        images = self.rasterizer.rasterize(input_pdf_path=pdfpath, dpi=72)
        doc.annotate_images(images=images)

        logger.info("Predicting words...")
        words = self.word_predictor.predict(document=doc)
        doc.annotate(words=words)

        logger.info("Predicting blocks...")
        layout = self.effdet_publaynet_predictor.predict(document=doc)
        equations = self.effdet_mfd_predictor.predict(document=doc)

        # we annotate layout info in the document
        doc.annotate(layout=layout)

        # list annotations separately
        doc.annotate(equations=equations)

        # blocks are used by IVILA, so we need to annotate them as well
        doc.annotate(blocks=layout + equations)

        logger.info("Predicting vila...")
        vila_span_groups = self.vila_predictor.predict(document=doc)
        doc.annotate(vila_span_groups=vila_span_groups)

        return doc
