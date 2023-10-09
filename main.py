from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
import requests
import json
import os


headers = {
        'authority': 'mangalivre.net',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-requested-with': 'XMLHttpRequest'
    }

def get_gofile_server():
    url = "https://api.gofile.io/getServer"
    response = requests.get(url, data={})
    return response.json().get("data").get("server")

def upload_to_gofile_and_get_link(pdfPath):
    url = f"https://{get_gofile_server()}.gofile.io/uploadFile"
    
    files = {
        'file': open(pdfPath, 'rb')
    }
    
    response = requests.post( url, files=files, data={})
    return response.json().get("data").get("downloadPage")

def search_manga(name):
    url = "https://mangalivre.net/lib/search/series.json"

    payload = f"search={name}"

    response = requests.post(url, headers=headers, data=payload)

    return response.json().get("series")


def get_chapter(id_serie, number_chapter, page=1):
    url = f"https://mangalivre.net/series/chapters_list.json?page={page}&id_serie={id_serie}"
    
    try:
        response = requests.request("GET", url, headers=headers, data={})

        if response.status_code == 200:
            for chapter in response.json().get('chapters'):
                if (chapter.get('number') == number_chapter):
                    release_scan = list(chapter.get("releases").keys())[0]
                    return chapter.get("releases").get(release_scan).get("id_release")
                
            return get_chapter(id_serie, number_chapter, page + 1)
        else:
            print(f"Capítulo {number_chapter} não encontrado - " + response.text)
    except Exception as e:
        print(f"Erro para encontrar capítulo {number_chapter} - {e}")


def get_page(id_release):
    url = f"https://mangalivre.net/leitor/pages/{id_release}.json"
    response = requests.get(url, headers=headers, data={})
    pages = []
    for page in response.json().get("images"):
        pages.append(page.get("legacy"))
    return pages


def save_chapter_pages(manga_name, chapter_number, pages):
    
    folder = f"mangas/{manga_name}"
    if not os.path.exists(folder):
        os.makedirs(folder)
            
    pdfPath = f"{folder}/{manga_name}_{chapter_number}.pdf"
    
    width, height = A4
    c = canvas.Canvas(pdfPath, pagesize=A4)

    for page in pages:
        #print(f"Baixando {page}")
        response = requests.get(page, headers=headers, data={})
        
        if response.status_code == 200:
            imgPath = f"{folder}/{page.split('/')[-1]}"
            
            if imgPath[-4:] != ".jpg" and imgPath[-4:] != ".png":
                #print('Arquivo não é uma imagem')
                continue
            
            with open(imgPath, 'wb') as f:
                f.write(response.content)
                
            with Image.open(imgPath) as img:
                
                iwidth, iheight = img.size

                aspect_ratio = iwidth / iheight
                
                if aspect_ratio > 1:
                    c.drawImage(imgPath, 0, 0, width=width*2, height=height)
                    c.showPage()
                    c.drawImage(imgPath, -width, 0, width=width*2, height=height)
                    c.showPage()
                else:
                    c.drawImage(imgPath, 0, 0, width=width, height=height)
                    c.showPage()
            
            os.remove(imgPath)
            
        else:
            print(f"Erro ao baixar página {page} - " + response.text)
            
    c.save()
    
    print('Criando link de download...')
    download_link = upload_to_gofile_and_get_link(pdfPath)
    print(f'link de download (Capitulo {chapter_number}): {download_link}')
    
    #os.remove(pdfPath)
    
    return chapter_number, download_link


def main():
    while True:
        name = input("Digite o nome do manga: ")
        mangas = search_manga(name)

        print("=================== Mangas Encontrados ======================")
        if(mangas == False):
            print("Nenhum manga encontrado")
            print("=============================================================")
            exit()
        for manga in mangas:
            print(f"{manga.get('id_serie')} - {manga.get('name')}")
        print("=============================================================")

        id_serie = input("Digite o id do manga (número ao lado do nome): ")
        for manga in mangas:
            if manga.get('id_serie') == id_serie:
                name = manga.get('name')
                break
        chapter = input("Digite o capítulo inicial: ")
        chapter2 = input("Digite o capítulo final: ")
        if chapter2 == "":
            chapter2 = int(chapter)
        print(f'Procurando capítulos de {chapter} a {chapter2}...')
        
        download_links = []
        
        for chapter in range(int(chapter), int(chapter2) + 1):
            id_release = get_chapter(id_serie, str(chapter))
            pages = get_page(id_release)
            print(f"====================== Páginas Encontradas Capítulo {chapter} =========================")
            print(json.dumps(pages, indent=4))
            print("Baixando...")

            download_links.append(save_chapter_pages(name, str(chapter), pages))
            print("Capítulo baixado com sucesso!")
            
        for download_link in download_links:
            print(f"Link de download (Capítulo {download_link[0]}): {download_link[1]}")


if __name__ == "__main__":
    main()