import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

class FritzPDFDownloader:
    """Download PDF reports from fritz.freiburg.de website"""
    
    def __init__(self, base_url="https://www.freiburg.de/pb/207932.html"):
        self.base_url = base_url
        self.download_dir = Path("data/pdfs")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def extract_pdf_links(self, html_content):
        """Extract PDF download links from the Fritz publications page using BeautifulSoup"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        pdf_links = []
        
        # Find all links that point to PDFs
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.pdf' in href.lower() and 'lesen' in link.get_text().lower():
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = urljoin("https://www.freiburg.de", href)
                else:
                    full_url = href
                
                # Extract size information (often in parentheses after the link)
                size_text = ""
                next_element = link.next_sibling
                if next_element and '(' in str(next_element):
                    size_text = str(next_element).strip()
                
                # Extract document title from surrounding content
                title = self.extract_document_title(link)
                
                pdf_links.append({
                    'url': full_url,
                    'size': size_text,
                    'title': title,
                    'filename': self.generate_filename(title, full_url)
                })
        
        return pdf_links
    
    def extract_document_title(self, link):
        """Extract document title from the surrounding HTML context"""
        # Look for bold text before the link
        parent = link.parent
        if parent:
            bold_elements = parent.find_all('strong')
            if bold_elements:
                return bold_elements[0].get_text().strip()
        
        # Fallback to link text
        return link.get_text().strip()
    
    def generate_filename(self, title, url):
        """Generate a clean filename from title and URL"""
        if title and title != "lesen":
            filename = title
            # Clean up title for filename
            filename = filename.replace(' ', '_')
            filename = filename.replace('/', '_')
            filename = filename.replace('\\', '_')
            filename = filename.replace(':', '_')
            filename = filename.replace('*', '_')
            filename = filename.replace('?', '_')
            filename = filename.replace('"', '_')
            filename = filename.replace('<', '_')
            filename = filename.replace('>', '_')
            filename = filename.replace('|', '_')
            
            # Remove special characters and umlauts
            filename = filename.replace('ä', 'ae')
            filename = filename.replace('ö', 'oe')
            filename = filename.replace('ü', 'ue')
            filename = filename.replace('ß', 'ss')
            filename = filename.replace('Ä', 'Ae')
            filename = filename.replace('Ö', 'Oe')
            filename = filename.replace('Ü', 'Ue')
            
            # Limit length and add extension
            filename = filename[:100]  # Reasonable filename length
            if not filename.endswith('.pdf'):
                filename += '.pdf'
        else:
            # Fallback to URL-based filename
            parsed = urlparse(url)
            filename = Path(parsed.path).name
            if not filename.endswith('.pdf'):
                filename += '.pdf'
        
        return filename
    
    def download_pdf(self, pdf_info):
        """Download a single PDF file"""
        url = pdf_info['url']
        filename = pdf_info['filename']
        filepath = self.download_dir / filename
        
        # Skip if already downloaded
        if filepath.exists():
            logger.info(f"⏭️ Skipping {filename} - already exists")
            return True
            
        try:
            logger.info(f"📥 Downloading: {pdf_info['title']} -> {filename}")
            if pdf_info['size']:
                logger.info(f"   Size: {pdf_info['size']}")
            
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            logger.success(f"✅ Downloaded {filename} ({total_size:,} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download {filename}: {e}")
            if filepath.exists():
                filepath.unlink()  # Remove partial file
            return False
    
    def download_all(self):
        """Download all Fritz PDFs"""
        logger.info("🚀 Starting Fritz PDF downloader...")
        logger.info(f"📂 Download directory: {self.download_dir.absolute()}")
        
        try:
            logger.info("🌐 Fetching Fritz publications page...")
            
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            pdf_links = self.extract_pdf_links(html_content)
            logger.info(f"🔍 Found {len(pdf_links)} PDF documents")
            
            if not pdf_links:
                logger.warning("No PDFs found! This might indicate a parsing issue.")
                return 0
            
            successful_downloads = 0
            for i, pdf_info in enumerate(pdf_links, 1):
                logger.info(f"📋 Processing {i}/{len(pdf_links)}")
                
                if self.download_pdf(pdf_info):
                    successful_downloads += 1
                
                # Be nice to the server
                time.sleep(2)
            
            logger.success(f"🎉 Completed! Downloaded {successful_downloads}/{len(pdf_links)} PDFs successfully")
            return successful_downloads
            
        except Exception as e:
            logger.error(f"💥 Failed to fetch publications page: {e}")
            return 0

if __name__ == "__main__":
    downloader = FritzPDFDownloader()
    success_count = downloader.download_all()
    
    if success_count > 0:
        logger.info(f"✨ All done! Check the data/pdfs folder for {success_count} downloaded files.")
    else:
        logger.error("😞 No files were downloaded. Please check the logs above for errors.")
