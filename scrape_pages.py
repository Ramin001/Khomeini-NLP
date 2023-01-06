import pandas as pd
pd.set_option('display.max_rows', 100)

# setting chrome driver according to this thread: https://stackoverflow.com/questions/29858752/error-message-chromedriver-executable-needs-to-be-available-in-the-path
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class sahife_page:
    def __init__(self,driver):
        self.driver = driver
        #type of document (letter, speech, etc.)
        self.type = self.driver.find_elements(By.XPATH, "//div[@class='title']")[0].text.strip()
        
        #body text
        txt = ''
        for i in range(len(self.driver.find_elements(By.XPATH, "//div[@class='body']"))):
            txt=txt+self.driver.find_elements(By.XPATH, "//div[@class='body']")[i].text
        self.body = txt
        
        #parse header information
        self.header = self.driver.find_elements(By.XPATH, "//div[@class='header']")[0].text

        self.addressed_to = self.header.partition('مخاطب: ')[2]
        self.subject = self.header.partition('مخاطب: ')[0].partition('موضوع: ')[2]
        self.place = self.header.partition('موضوع: ')[0].partition('مکان: ')[2]
        self.date_string = self.header.partition('مکان: ')[0].partition('زمان: ')[2]
        try:
            self.day = self.date_string.split()[0]
            self.month = self.date_string.split()[1]
            self.year = self.date_string.split()[2]
        except IndexError:
            self.day = ''
            self.month = ''
            self.year = ''
        
    def to_dict(self):
        return {
            'subject': self.subject,
            'type': self.type,
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'place': self.place,
            'addressed_to': self.addressed_to,
            'body': self.body,
            'full_date': self.date_string
        }



#get links to all title pages
page_link_list = []
for vol in range(1,22):
    driver = webdriver.Chrome()
    driver.get('https://farsi.rouhollah.ir/library/sahifeh-imam-khomeini/vol/'+str(vol))  #open each volum's page
    page_link = driver.find_elements(By.TAG_NAME,'a')  #get title links
    print(page_link)
    for i in range(0,len(page_link)):
        page_link_list.append(page_link[i].get_attribute("href"))
page_link_list = [s for s in page_link_list if 'title' in s]  #drop other irrelevant links in the page
with open('./data/page_link_list.txt', 'w') as f:
    for line in page_link_list:
        f.write(f"{line}\n")




#save contents of each page in a dataframe

driver = webdriver.Chrome()

sahife_pages = []
problematic_links = []
for link in page_link_list:
    driver.get(link)
    time.sleep(2)
    try:
        page_info = sahife_page(driver).to_dict()
        sahife_pages.append(page_info)
    except IndexError:
        problematic_links.append(link)

sahife_df = pd.DataFrame.from_records(sahife_pages) 
sahife_df['type'] = [drop_punc(s) for s in sahife_df['type']]

#clean dates
month_list = ['فروردین','اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن',  'اسفند']
sahife_df['shamsi_date'] = [str(s).split('/')[0] for s in sahife_df['full_date']]
sahife_df['month'] = [ [subs for subs in str(s).split(' ') if subs in month_list] for s in sahife_df['full_date']]
[s.append('') for s in sahife_df['month']]
sahife_df['month'] = [s[0] for s in sahife_df['month']]

sahife_df['numerics'] = [ [subs for subs in s.split(' ') if subs.isdigit()  ] for s in sahife_df['shamsi_date']]
sahife_df['day'] = [ [i for i in s if int(i)<32  ] for s in sahife_df['numerics']]
[i.append('') for i in sahife_df['day']]
sahife_df['day'] = [s[0] for s in sahife_df['day']]
sahife_df['day'] = pd.to_numeric(sahife_df['day'])

sahife_df['year'] = [ [i for i in s if int(i)>1300  ] for s in sahife_df['numerics']]
[i.append('') for i in sahife_df['year']]
sahife_df['year'] = [s[0] for s in sahife_df['year']]
sahife_df['year'] = pd.to_numeric(sahife_df['year'])

sahife_df = sahife_df.drop(columns=['shamsi_date','numerics'])

#save the final dataframe which is the main data
sahife_df.to_excel("./data/sahifeh.xlsx")