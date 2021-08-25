import time
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class Disc():
    def __init__(self):
        self.name = ''
        self.manufacturer = ''
        self.price = ''
        self.store = ''
        self.url = ''

class Scraper():
    def __init__(self, disc_search):
        self.url = ''
        self.search_url = ''
        self.disc_search = disc_search
        self.discs = []
    
    def get_chrome(self):
        opt = webdriver.ChromeOptions()
        opt.add_argument("--headless")
        opt.add_argument("--disable-extensions")
        opt.add_argument("--disable-gpu")
        opt.add_argument("--disable-xss-auditor")
        #opt.add_argument("--disable-web-security")
        #opt.add_argument("--allow-running-insecure-content")
        #opt.add_argument("--no-sandbox")
        opt.add_argument("--disable-setuid-sandbox")
        opt.add_argument("--disable-webgl")
        opt.add_argument("--disable-popup-blocking")
        opt.page_load_strategy = 'eager'
        browser = webdriver.Chrome(options=opt)
        browser.implicitly_wait(10)
        browser.set_page_load_timeout(30)
        return browser

    async def scrape(self):
        pass

class DiscInStock(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.search_url = f'https://www.discinstock.no/?name={disc_search}'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=')
            driver.get(url)
            time.sleep(1)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            for a in soup.findAll("div", class_="col"):
                disc = Disc()
                disc.manufacturer = a.find("h6", class_="text-muted font-monospace h-100").getText()
                disc.name = a.find("span", class_="fs-5").getText()                
                disc.price = a.find("span", class_="flex-shrink-1 display-6 mt-1").getText()
                disc.store = a.find("span", class_="mx-auto text-muted").getText()
                link = a.find('a', href=True)
                disc.url = link['href']

                self.discs.append(disc)

class FrisbeeFeber(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.url = 'frisbeefeber.no'
        self.search_url = f'https://www.frisbeefeber.no/search_result?keywords={disc_search}'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&')
            driver.get(url)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            for product in soup.select('li[class*="product-box-id-"]'):
                # Is product in stock ?
                not_in_stock = product.find("div", class_="product not-in-stock-product")
                if (not_in_stock is not None):
                    continue
                disc = Disc()
                disc.name = product.find("a", class_="title col-md-12").getText()
                # Search engine gives false results, check if the disc name is correct
                if (self.disc_search.lower() not in disc.name.lower()):
                    continue
                div_manufacturer = product.find("div", class_="manufacturer-box")
                alt_manufacturer = div_manufacturer.find("img", alt=True)
                disc.manufacturer = alt_manufacturer['alt']
                disc.price = product.find("div", class_="price col-md-12").getText()
                disc.store = self.url
                url = product.find('a', href=True)
                disc.url = url['href']

                self.discs.append(disc) 

# Sune Sport does not contain disc manufacturer
class SuneSport(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.url = 'sunesport.no'
        self.search_url = f'https://sunesport.no/product/search.html?search={disc_search}&category_id=268&sub_category=true'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&')
            driver.get(url)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            for product in soup.findAll("div", class_="product-thumb"):
                if (product.find("span", class_="stock-status").getText() == "Utsolgt"):
                    continue

                disc = Disc()
                caption = product.find("div", class_="caption")
                h4 = caption.find("h4")
                a = h4.find('a', href=True)
                disc.name = a.getText()
                disc.url = a["href"]
                disc.price = re.search(r" (.*?)Ekskl.", caption.find("p", class_="price").getText()).group(1)
                disc.store = self.url
                self.discs.append(disc)

class Xxl(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search.replace(" ", "+"))
        self.url = 'xxl.no'
        self.product_url = 'https://www.xxl.no'
        self.search_url = f'https://www.xxl.no/search?query={self.disc_search}&sort=relevance&Frisbeegolffilters_string_mv=Driver&Frisbeegolffilters_string_mv=Putter&Frisbeegolffilters_string_mv=Mid+range+frisbee'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&+')
            driver.get(url)
            time.sleep(1)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")
            contain_discs = False

            for filter in soup.findAll("div", class_="MuiAccordionSummary-content jss11 Mui-expanded jss12"):
                if "Frisbeegolf" in filter.getText():
                    contain_discs = True

            if (contain_discs == False):
                return

            product_list = soup.find("ul", class_="product-list product-list--multiline")
            for product in product_list.findAll("li"):                
                disc = Disc()
                product_info = product.find("div", class_="product-card__info-wrapper")
                disc.name = product_info.find("p").getText().split(", ")[0]
                disc.manufacturer = product_info.find("h3").getText()
                product_price = product.find("div", class_="product-card__price-wrapper")                
                disc.price = product_price.find("p").getText()
                a = product.find('a', href=True)
                disc.url = f'{self.product_url}{a["href"]}'
                disc.store = self.url
                self.discs.append(disc)

# Discexpress does not contain disc manufacturer
class DiscExpress(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.url = 'discexpress.se'
        self.url_product = 'https://www.discexpress.se'
        self.search_url = f'https://www.discexpress.se/a/search?type=product&q={disc_search}'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&')
            driver.get(url)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            for grid_item in soup.findAll("div", class_="grid-item search-result large--one-fifth medium--one-third small--one-half"):
                if (self.disc_search.lower() not in grid_item.find("p").getText().lower()): # Search engine gives false response
                    continue

                disc = Disc()
                disc.name = grid_item.find("p").getText()
                a = grid_item.find('a', href=True)
                disc.url = f'{self.url_product}{a["href"]}'
                for hidden_item in grid_item.findAll("span", class_="visually-hidden"):
                    if("kr" in hidden_item.getText().lower()):
                        disc.price = hidden_item.getText()                 
                disc.store = self.url
                self.discs.append(disc)

class Discconnection(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.url = 'discconnection.dk'
        self.search_url = f'https://discconnection.dk/default.asp?page=productlist.asp&Search_Hovedgruppe=&Search_Undergruppe=&Search_Producent=&Search_Type=&Search_Model=&Search_Plastic=&PriceFrom=&PriceTo=&Search_FREE={disc_search}'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&')
            driver.get(url)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")
            
            names = []
            manufacturers = []
            prices = []

            # Contains: "Innova Firebird  •  Plastic: Champion  •  Driver"
            for prodHeader in soup.findAll("td", class_="prodHeader"):
                b = prodHeader.find_all("b")
                prodHeader_list = b[0].getText().split()
                manufacturers.append(prodHeader_list[0])
                names.append(b[0].getText())

            # Contains: Pris inkl. moms: 120,00 DKK
            for prodPriceWeight in soup.findAll("td", class_="prodPriceWeight"):
                b = prodPriceWeight.find("b")
                if b is not None:
                    prices.append(b.getText())            

            for i in range(len(names)):
                disc = Disc()
                disc.name = names[i]
                disc.manufacturer = manufacturers[i]
                disc.price = prices[i]
                disc.store = self.url
                disc.url = url
                self.discs.append(disc)

class Discsport(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.url = 'discsport.se'
        self.search_url = f'https://discsport.se/shopping/?search_adv=&name={disc_search}&selBrand=0&selCat=1&selType=0&selStatus=0&selMold=0&selDiscType=0&selStability=0&selPlastic=0&selPlasticQuality=0&selColSel=0&selColPrim=0&selCol=0&selWeightInt=0&selWeight=0&sel_speed=0&sel_glide=0&sel_turn=-100&sel_fade=-100&Submit='
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&')
            driver.get(url)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            products = soup.find('ul', class_="products")
            if (products is not None):
                for product in products.findAll("li"):
                    if product.find("div", class_="upperLeftLabel"): # Not in stock
                        continue
                    disc = Disc()
                    a = product.find("h3", class_="shop_item").find('a', href=True)
                    disc.name = a.getText().replace("\n", " ").replace("\t", " ")
                    disc.url = a["href"]
                    manufacturer = re.search(r"]<br/>(.*?)\|", a["title"]).group(1).replace("\xa0", "")
                    if (manufacturer is not None):
                        disc.manufacturer = manufacturer                    
                    disc.price = product.find("div", class_="text-center").find("p").getText()
                    disc.store = self.url
                    self.discs.append(disc)

# Latitude64
class Latitude64(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.url = 'store.latitude64.se'
        self.url_product = 'https://store.latitude64.se/'
        self.search_url = f'https://store.latitude64.se/search?q={disc_search}'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&')
            driver.get(url)
            time.sleep(1)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            for prodHeader in soup.findAll("div", class_="box product"):
                title =  prodHeader.find("a", class_="title")
                if (title is None):
                    continue
                disc = Disc()
                disc.name = title.getText()
                disc.url = f'{self.url_product}{title["href"]}'
                disc.manufacturer = prodHeader.find("span", class_="vendor").getText()
                disc.price = prodHeader.find("span", class_="money").getText()
                disc.store = self.url
                self.discs.append(disc)

# DiscRepublic
class Discrepublic(Scraper):
    def __init__(self, disc_search):
        super().__init__(disc_search)
        self.url = 'discrepublic.ca'
        self.url_product = 'https://discrepublic.ca'
        self.search_url = f'https://discrepublic.ca/search?type=product&collection=in-stock&q=*{disc_search}*'
    
    def scrape(self):
        with self.get_chrome() as driver:
            url = urllib.parse.quote(self.search_url, safe='?:/=&')
            driver.get(url)
            time.sleep(1)
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            # Check if the disc is sold out
            for product in soup.findAll("div", class_="product-item-wrapper col-sm-2"):
                if product.find("span", class_="sold_out"):
                    continue

                # mold contain the disc name, must check this field
                mold = product.find("span", class_="mold").getText()
                plastic = product.find("span", class_="plastic")
                # Is the product a disc?
                if plastic is None:
                    continue                
                if self.disc_search.lower() not in f'{mold.lower()} {plastic.getText().lower()}':
                    continue

                disc = Disc()
                disc.name = f'{mold} {plastic.getText()}'
                product_title = product.find("div", class_="product-title")                
                title = product_title.find('a', href=True)
                # manufacturer is fetched from an alt string
                img = product.find('img', class_="not-rotation img-responsive front")
                disc.manufacturer = img["alt"].split(" ")[0]
                disc.url = f'{self.url_product}{title["href"]}'

                # If the disc is on sale, there is two prices. Check and use correct
                normal_price = product.find("span", class_="price_sale price_normal")
                if normal_price is None:
                    disc.price = product.find("span", class_="price_sale").getText().replace("\n", "")
                else:
                    disc.price = normal_price.getText().replace("\n", "")
                disc.store = self.url                

                self.discs.append(disc)
