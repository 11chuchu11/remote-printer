from pypdf import PdfWriter
import pages


def _make_pdf(path, n_pages):
    writer = PdfWriter()
    for _ in range(n_pages):
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)


class TestCountPages:
    def test_counts_real_pdf_pages(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        _make_pdf(pdf, 5)
        assert pages.count_pages(str(pdf)) == 5

    def test_non_pdf_file_counts_as_one(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"not a real jpg, doesn't matter")
        assert pages.count_pages(str(img)) == 1

    def test_corrupt_pdf_falls_back_to_one(self, tmp_path):
        pdf = tmp_path / "broken.pdf"
        pdf.write_bytes(b"this is not a valid pdf")
        assert pages.count_pages(str(pdf)) == 1


class TestResolvePrintedPages:
    def test_all_returns_total(self):
        assert pages.resolve_printed_pages(10, "all") == 10

    def test_empty_string_treated_as_all(self):
        assert pages.resolve_printed_pages(10, "") == 10

    def test_odd_on_even_total(self):
        assert pages.resolve_printed_pages(10, "odd") == 5

    def test_odd_on_odd_total(self):
        assert pages.resolve_printed_pages(7, "odd") == 4

    def test_even_on_even_total(self):
        assert pages.resolve_printed_pages(10, "even") == 5

    def test_even_on_odd_total(self):
        assert pages.resolve_printed_pages(7, "even") == 3

    def test_custom_range(self):
        assert pages.resolve_printed_pages(10, "1-3,5,7-9") == 7

    def test_custom_range_dedupes_overlap(self):
        assert pages.resolve_printed_pages(10, "1-3,2-4") == 4

    def test_custom_range_clamps_to_total(self):
        assert pages.resolve_printed_pages(5, "1-3,10,20") == 3
