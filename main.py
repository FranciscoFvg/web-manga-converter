from PIL import Image 
import requests
import img2pdf 
import PyPDF2
import shutil
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
    # Create folder if not exists
    folders = [
        f"mangas/{manga_name}/{chapter_number}",
        f"mangas/{manga_name}/{chapter_number}/imgs",
        f"mangas/{manga_name}/{chapter_number}/pdfs"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            
    merger = PyPDF2.PdfMerger()

    for page in pages:
        print(f"Baixando {page}")
        response = requests.get(page, headers=headers, data={})
        
        if response.status_code == 200:
            imgPath = f"{folders[1]}/{page.split('/')[-1]}"
            
            if imgPath[-4:] != ".jpg" and imgPath[-4:] != ".png":
                print('Arquivo não é uma imagem')
                continue
            
            with open(imgPath, 'wb') as f:
                f.write(response.content)
            
            pdfPath = f"{folders[2]}/{page.split('/')[-1][0:-4]}.pdf"
            
            image = Image.open(imgPath) 
            pdf_bytes = img2pdf.convert(image.filename) 
            with open(pdfPath, 'wb') as file:
                file.write(pdf_bytes) 
            image.close() 
                    
            merger.append(pdfPath)
            print("Arquivo pdf criado com sucesso!") 
        else:
            print(f"Erro ao baixar página {page} - " + response.text)
            
    merged_pdf_path = f"{folders[0]}/{manga_name}_{chapter_number}.pdf"
    with open(merged_pdf_path, 'wb') as merged_pdf:
        merger.write(merged_pdf)
        
    merger.close()
    shutil.rmtree(folders[1])
    shutil.rmtree(folders[2])


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
        
        for chapter in range(int(chapter), int(chapter2) + 1):
            id_release = get_chapter(id_serie, str(chapter))
            pages = get_page(id_release)
            print("====================== Páginas Encontradas =========================")
            print(json.dumps(pages, indent=4))

            print("=================== Deseja baixar o capítulo? ======================")
            print("1 - Sim")
            print("2 - Não")
            print("====================================================================")
            option = "1"#input("Digite a opção: ")
            if option == "1":
                save_chapter_pages(name, str(chapter), pages)
                print("Capítulo baixado com sucesso!")


if __name__ == "__main__":
    main()