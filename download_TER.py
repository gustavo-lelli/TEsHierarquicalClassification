import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import download_fasta

def merge_gff3_files(input_files, output_file):
	""" Junta vários arquivos .gff3 em um único arquivo, garantindo que os cabeçalhos sejam mantidos apenas uma vez. """
	with open(output_file, 'w') as out_f:
		header_written = False  # Para evitar múltiplos cabeçalhos

		for file in input_files:
			with open(file, 'r') as in_f:
				for line in in_f:
					if line.startswith("##") and header_written:
						continue  # Ignora cabeçalhos repetidos
					if line.startswith("##") and not header_written:
						header_written = True  # Escreve o cabeçalho apenas uma vez
					out_f.write(line)
			os.remove(file)  # Remove o arquivo original

	print(f"Arquivo combinado salvo em: {output_file}")

def get_genome_accession(organism_name):
	base_url = "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/taxon/"

	# Substitui espaços por %20 (ou usa requests para lidar automaticamente)
	taxon_url = base_url + f"{organism_name}/dataset_report"

	response = requests.get(taxon_url)

	if response.status_code == 200:
		data = response.json()
		if "reports" in data and data["reports"]:
			accession = data["reports"][0]["accession"]
			return accession
		else:
			print("Nenhuma accession encontrada para esta espécie.")
			return None
	else:
		print(f"Erro ao buscar accession (Status: {response.status_code})")
		return None

if __name__ == "__main__":
	# URL da página com os links das classes
	url_base = "http://apte.cp.utfpr.edu.br/download"

	# Criar diretório base se não existir
	output_dir = "data"
	os.makedirs(output_dir, exist_ok=True)

	# Obter o conteúdo da página
	response = requests.get(url_base)
	soup = BeautifulSoup(response.text, 'html.parser')

	# Procurar todas as tabelas e links de download
	for row in soup.find_all("tr"):  # Itera pelas linhas da tabela
		columns = row.find_all("td")
		if columns:
			species_name = columns[0].text.strip().split(" - ")[0].replace(". ", "")  # Nome da espécie sem o número de TEs
			species_name = species_name.replace(species_name[1],  species_name[1].upper(), 1)  # Corrige a capitalização

			species_dir = os.path.join(output_dir, species_name)
			os.makedirs(species_dir, exist_ok=True)  # Criar pasta para a espécie

			gff3_files = []

			# Itera pelos links de download
			for col in columns[1:]:  # Ignora a primeira coluna (nome da espécie)
				link = col.find("a")
				if link and "download" in link.text.lower():
					file_url = urljoin(url_base, link['href'])  # Constrói o URL absoluto
					file_name = file_url.split("/")[-1]

					# Obter accession do genoma
					organism_name = file_url.split("/")[-2].replace("_", " ")

					if file_name == "TEAnnotationFinal.gff3":
						continue # Ignora o arquivo TEAnnotationFinal.gff3

					file_path = os.path.join(species_dir, file_name)

					# Baixar o arquivo
					with requests.get(file_url, stream=True) as file_resp:
						if file_resp.status_code == 200:
							with open(file_path, "wb") as f:
								for chunk in file_resp.iter_content(chunk_size=8192):
									f.write(chunk)
							gff3_files.append(file_path)
							print(f"Baixado: {file_path}")
						else:
							print(f"Erro ao baixar {file_url}")

			merge_gff3_files(gff3_files, os.path.join(species_dir, f"{species_name}_TER_merged.gff3"))

			# Baixar o arquivo FASTA
			accession = get_genome_accession(organism_name)
			if accession:
				download_fasta.baixar_fasta(accession, species_name)
				print()
			else:
				print("Não foi possível baixar o arquivo FASTA.")