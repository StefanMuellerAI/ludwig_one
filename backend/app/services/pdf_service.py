"""
PDF Service - Handle all PDF operations
Uses PyMuPDF (fitz) for performance
"""
import io
import logging
from typing import List, Tuple, AsyncIterator
import fitz  # PyMuPDF
from pypdf import PdfWriter, PdfReader

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF operations"""

    @staticmethod
    async def extract_text_and_images(pdf_blob: bytes) -> Tuple[str, List[bytes]]:
        """
        Extract all text and images from a PDF.

        Args:
            pdf_blob: PDF file as bytes

        Returns:
            Tuple of (full_text, list of image bytes)
        """
        try:
            doc = fitz.open(stream=pdf_blob, filetype="pdf")
            full_text = ""
            images = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extract text
                page_text = page.get_text()
                if page_text:
                    full_text += f"\n--- Page {page_num + 1} ---\n"
                    full_text += page_text

                # Extract images
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        images.append(image_bytes)
                        logger.debug(f"Extracted image {img_index + 1} from page {page_num + 1}")
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index + 1} from page {page_num + 1}: {e}")

            doc.close()
            logger.info(f"Extracted {len(images)} images and {len(full_text)} characters of text")
            return full_text, images

        except Exception as e:
            logger.error(f"Failed to extract from PDF: {e}")
            raise

    @staticmethod
    async def split_pdf_into_pages(pdf_blob: bytes) -> AsyncIterator[Tuple[int, bytes]]:
        """
        Split PDF into individual pages.

        Args:
            pdf_blob: PDF file as bytes

        Yields:
            Tuples of (page_number, page_pdf_bytes)
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_blob))
            total_pages = len(reader.pages)
            logger.info(f"Splitting PDF into {total_pages} pages")

            for page_num in range(total_pages):
                try:
                    writer = PdfWriter()
                    writer.add_page(reader.pages[page_num])

                    # Write to bytes
                    output = io.BytesIO()
                    writer.write(output)
                    page_bytes = output.getvalue()

                    yield (page_num + 1, page_bytes)
                    logger.debug(f"Split page {page_num + 1}/{total_pages}")

                except Exception as e:
                    logger.error(f"Failed to split page {page_num + 1}: {e}")
                    raise

        except Exception as e:
            logger.error(f"Failed to split PDF: {e}")
            raise

    @staticmethod
    async def merge_pdfs(pdf_blobs: List[bytes]) -> bytes:
        """
        Merge multiple PDFs into one.

        Args:
            pdf_blobs: List of PDF files as bytes

        Returns:
            Merged PDF as bytes
        """
        try:
            writer = PdfWriter()

            for idx, pdf_blob in enumerate(pdf_blobs):
                try:
                    reader = PdfReader(io.BytesIO(pdf_blob))
                    for page in reader.pages:
                        writer.add_page(page)
                    logger.debug(f"Added PDF {idx + 1}/{len(pdf_blobs)} to merge")
                except Exception as e:
                    logger.error(f"Failed to add PDF {idx + 1} to merge: {e}")
                    raise

            # Write merged PDF to bytes
            output = io.BytesIO()
            writer.write(output)
            merged_bytes = output.getvalue()

            logger.info(f"Merged {len(pdf_blobs)} PDFs into {len(merged_bytes)} bytes")
            return merged_bytes

        except Exception as e:
            logger.error(f"Failed to merge PDFs: {e}")
            raise

    @staticmethod
    async def get_page_count(pdf_blob: bytes) -> int:
        """
        Get number of pages in PDF.

        Args:
            pdf_blob: PDF file as bytes

        Returns:
            Number of pages
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_blob))
            return len(reader.pages)
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            raise

    @staticmethod
    async def extract_first_n_pages(pdf_blob: bytes, n: int = 3) -> Tuple[str, List[bytes]]:
        """
        Extract text and images from first N pages only.
        Useful for context management in merge decisions.

        Args:
            pdf_blob: PDF file as bytes
            n: Number of pages to extract (default 3)

        Returns:
            Tuple of (text, images) from first N pages
        """
        try:
            doc = fitz.open(stream=pdf_blob, filetype="pdf")
            full_text = ""
            images = []

            max_pages = min(n, len(doc))

            for page_num in range(max_pages):
                page = doc[page_num]

                # Extract text
                page_text = page.get_text()
                if page_text:
                    full_text += f"\n--- Page {page_num + 1} ---\n"
                    full_text += page_text

                # Extract images
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        images.append(image_bytes)
                    except Exception as e:
                        logger.warning(f"Failed to extract image: {e}")

            doc.close()
            logger.info(f"Extracted first {max_pages} pages: {len(images)} images, {len(full_text)} chars")
            return full_text, images

        except Exception as e:
            logger.error(f"Failed to extract first N pages: {e}")
            raise


# Global instance
pdf_service = PDFService()
