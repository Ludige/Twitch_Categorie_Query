from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

categories_list = []
        
class Principal(webdriver.Chrome):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = Service(ChromeDriverManager().install())
        super(Principal, self).__init__(service=service,options=options)
        self.maximize_window()

    def coletar_dados(self):
        self.get("https://www.twitch.tv/directory?sort=VIEWER_COUNT")
        time.sleep(10)
        
        import psycopg2
        conn = psycopg2.connect(
            host = "localhost",
            port = "5432",
            user = "airflow",
            password = "airflow",
            dbname = "dados_twitch"
        )
        
        cursor = conn.cursor()
        
        sql = """
            CREATE TABLE IF NOT EXISTS categories_list(
                ID INT GENERATED BY DEFAULT AS IDENTITY,
                categories_name VARCHAR NOT NULL,
                categories_viewer_count VARCHAR NOT NULL
            )
            """
        cursor.execute(sql)
        
        
        try:
            for i in range(2,20):
                if(i == 20):#Scroll
                    self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                categorie_name = WebDriverWait(self, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="browse-root-main-content"]/div[4]/div/div[1]/div['+str(i)+']/div/div/div/div/div[1]/div/div/div/div/span/a/h2'))).text
                categorie_viewer_count = WebDriverWait(self, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="browse-root-main-content"]/div[4]/div/div[1]/div['+str(i)+']/div/div/div/div/div[1]/div/div/p/a'))).text
                
                categorie_name = categorie_name.replace("ó", "o").replace("ú","u").replace("Ó","O").replace("Ú","U")
                categorie_viewer_count = categorie_viewer_count.replace("espectadores", "").replace("viewers", "").replace(" mil ","").replace(" K ", "")

                sql = "INSERT INTO categories_list(categories_name, categories_viewer_count) values ('"+categorie_name+"','"+categorie_viewer_count+"')"
                categories_list.append((categorie_name,categorie_viewer_count))
                cursor.execute(sql)
                conn.commit()
                
            cursor.close()
            conn.close()
        except (Exception, psycopg2.Error) as error:
            print(error)
        
    def escrever_planilha(self):
        import pandas as pd
        from datetime import datetime

        file = pd.read_excel("results/resultado.xlsx", engine='openpyxl', dtype=str)
        
        for i in range(len(categories_list)):
            file.at[i,'Categoria'] = categories_list[i][0]
            file.at[i,'Quantidade de Visualizações'] = categories_list[i][1]
            
        current_time = datetime.now()
        current_time = current_time.strftime('%Y-%m-%d %H-%M')
        file.to_excel(f"results/coleta/{current_time}.xlsx",index=False)
        
if __name__ == "__main__":
    bot = Principal()
    bot.coletar_dados()
    bot.escrever_planilha()