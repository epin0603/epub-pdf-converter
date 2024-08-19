import tkinter as tk
import ebooklib
import threading
from tkinter import filedialog, messagebox, ttk
from ebooklib import epub
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup

class ConverterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.progress = None
        self.progress_window = None

    def epub_to_pdf(self, epub_path, pdf_path): ###Will add images on the next update. Simple text conversion for now
        book = epub.read_epub(epub_path)
        pdf = SimpleDocTemplate(pdf_path, pagesize=letter)
        items = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
        content = []

        styles = getSampleStyleSheet()
        normal_style = styles["Normal"]
        heading_style = styles["Heading1"]

        ###Will add images on the next update
        #image_dir = "temp_images"
        #if not os.path.exists(image_dir):
        #    os.makedirs(image_dir)

        total_items = len(items)
        idx = 0

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                html_content = item.get_body_content().decode('utf-8')
                soup = BeautifulSoup(html_content, 'html.parser')

                for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = element.get_text()

                    if element.name == 'p':
                        paragraph = Paragraph(text, normal_style)
                        content.append(paragraph)
                        content.append(Spacer(1, 0.2 * inch))
                    elif element.name.startswith('h'):
                        paragraph = Paragraph(text, heading_style)
                        content.append(paragraph)
                        content.append(Spacer(1, 0.3 * inch))

            idx += 1
            self.update_progress(idx, total_items)

        pdf.build(content)

        ###Destructor for the temp images
        #for img_file in os.listdir(image_dir):
        #    os.remove(os.path.join(image_dir, img_file))
        #os.rmdir(image_dir)

    def pdf_to_epub(self, pdf_path, epub_path): ###EXPERIMENTAL FEATURE: The file is processed, but there are too many formatting errors in the text###
        book = epub.EpubBook()
        book.set_identifier('sample123456') ##Must change so that it gathers the info automatically
        book.set_title('Sample Title') ##Must change so that it gathers the info automatically
        book.set_language('en') ##Must change so that it gathers the info automatically

        chapter = epub.EpubHtml(title="Chapter 1", file_name="chap_1.xhtml", lang="en") ###Must change so that it gathers the chapter divisions automatically

        reader = PdfReader(pdf_path)
        text_content = ""

        idx = 0

        for page in reader.pages:
            text_content += page.extract_text()
            idx += 1
            self.update_progress(idx + 1, len(reader.pages))

        soup = BeautifulSoup("<html><body></body></html", "html.parser")
        body_tag = soup.body

        for paragraph in text_content.split('\n'): ##Must find better way to split the paragraphs. Lots of formatting issues
            p_tag = soup.new_tag("p")
            p_tag.string = paragraph
            body_tag.append(p_tag)

        chapter.content = str(soup)

        book.add_item(chapter)

        book.toc = [epub.Link(chapter.file_name, "Chapter 1", "chap1"),] ###Must change so that it gathers the chapter divisions automatically
        book.spine = ["nav", chapter]

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        epub.write_epub(epub_path, book, {})

    def update_progress(self, current, total): ##Updates progress bar
        if self.progress:
            percentage = int((current / total) * 100)
            self.progress['value'] = percentage
            self.progress_window.update_idletasks()

    def show_progress(self): #Shows new window with progress bar
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title('Progress')
        self.progress_window.geometry("300x100")
        self.progress = ttk.Progressbar(self.progress_window, orient="horizontal", length=250, mode="determinate")
        self.progress.pack(pady=20)
        self.progress['maximum'] = 100
        self.progress['value'] = 0

    def convert(self):
        file_path = filedialog.askopenfilename()
        if file_path.endswith('.epub'):
            save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            if save_path:
                self.show_progress()
                thread = threading.Thread(target=self.epub_to_pdf, args=(file_path, save_path))
                thread.start()
                self.root.after(100, self.check_thread, thread)
        elif file_path.endswith('.pdf'):
            save_path = filedialog.asksaveasfilename(defaultextension=".epub", filetypes=[("EPUB files", "*.epub")])
            if save_path:
                self.show_progress()
                thread = threading.Thread(target=self.pdf_to_epub, args=(file_path, save_path))
                thread.start()
                self.root.after(100, self.check_thread, thread)
        else:
            messagebox.showerror("Error", "Unsuported file type. Please select an EPUB or PDF file.")

    def check_thread(self, thread):
        if thread.is_alive():
            self.root.after(100, self.check_thread, thread)
        else:
            self.progress_window.destroy()
            messagebox.showinfo("Success", "Conversion completed successfully!")

    def run(self):
        self.root.title("EPUB And PDF Converter")
        self.root.geometry("500x200")

        label = tk.Label(self.root, text="Convert EPUB to PDF or PDF to EPUB", font=("Helvetica-Bold", 16))
        label.pack(pady=10)
        label = tk.Label(self.root, text="Warning: PDF to EPUB feature still in early development phase.", font=("Helvetica", 10))
        label.pack(pady=5)
        self.convert_button = tk.Button(self.root, text="Choose File and Convert", command=self.convert, font=("Helvetica-Bold", 14))
        self.convert_button.pack(pady=20)

        self.root.mainloop()