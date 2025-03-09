import os
import sys
import requests
import zipfile
import shutil

# URL da API para buscar detalhes do assembly
NCBI_ASSEMBLY_API = "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/"

def get_chromosomes_from_gff3(gff3_file):
	"""
	Lê um arquivo .gff3 e extrai os cromossomos listados nele.
	Retorna um conjunto com os IDs dos cromossomos.
	"""
	chromosomes = set()
	
	with open(gff3_file, 'r') as file:
		for line in file:
			if line.startswith("#"):
				continue
			fields = line.strip().split("\t")
			if len(fields) > 0:
				chromosome_id = fields[0]  # A primeira coluna geralmente contém o ID do cromossomo
				chromosomes.add(chromosome_id)

	return chromosomes

def split_fna_by_chromosome(fna_file, gff3_file, output_folder):
	"""
	Separa um arquivo .fna em vários arquivos, um para cada cromossomo listado no .gff3.
	"""
	# Obtém os cromossomos válidos do arquivo .gff3
	valid_chromosomes = get_chromosomes_from_gff3(gff3_file)

	# Criando pasta de saída, se não existir
	os.makedirs(output_folder, exist_ok=True)

	output_file = None

	with open(fna_file, 'r') as fna:
		for line in fna:
			if line.startswith(">"):  # Nova sequência de cromossomo encontrada

				# Encontra qual cromossomo está presente na linha
				found_chromosome = next((chrom for chrom in valid_chromosomes if chrom in line), None)
				
				if found_chromosome:  # Verifica se está no GFF3
					if output_file:
						output_file.close()

					output_path = os.path.join(output_folder, f"{found_chromosome}.fasta")
					output_file = open(output_path, "w")
					output_file.write(line)  # Escreve a linha do cabeçalho

					valid_chromosomes.remove(found_chromosome)  # Remove o cromossomo da lista

					print(f"Criando arquivo: {output_path}")
				else:
					output_file = None  # Ignorar este cromossomo

			elif output_file:  # Escreve as sequências no arquivo correto
				output_file.write(line)

	if output_file:
		output_file.close()

def separar_cromossomos(arquivo_fna, pasta_saida):
	"""Separa um arquivo .fna em vários arquivos FASTA individuais para cada cromossomo."""

	# Garante que a pasta de saída existe
	os.makedirs(pasta_saida, exist_ok=True)

	with open(arquivo_fna, "r") as f:
		cromossomo = None
		conteudo = []

		for linha in f:
			if linha.startswith(">"):  # Novo cromossomo encontrado
				if cromossomo:
					# Salva o cromossomo anterior
					caminho_arquivo = os.path.join(pasta_saida, f"{cromossomo}.fasta")
					with open(caminho_arquivo, "w") as out_f:
						out_f.writelines(conteudo)
					print(f"Salvo: {caminho_arquivo}")

				# Extrai o identificador do cromossomo
				cromossomo = linha.split()[0][1:]  # Remove '>' e pega o ID
				conteudo = [linha]  # Reinicia o conteúdo com a nova linha de cabeçalho

			else:
				conteudo.append(linha)

		# Salva o último cromossomo
		if cromossomo:
			caminho_arquivo = os.path.join(pasta_saida, f"{cromossomo}.fasta")
			with open(caminho_arquivo, "w") as out_f:
				out_f.writelines(conteudo)
			print(f"Salvo: {caminho_arquivo}")


def baixar_fasta(genome_id, species_name):
	"""Baixa o arquivo FASTA para um genoma Assembly do NCBI."""
	species_dir = os.path.join("data", species_name, "fasta")
	os.makedirs(species_dir, exist_ok=True)

	# URL correta para acessar o genoma Assembly
	url = f"{NCBI_ASSEMBLY_API}{genome_id}/download"
	params = {"include_annotation_type": "GENOME_FASTA"}

	print(f"Baixando {genome_id}.fna da API de Assembly do NCBI...")
	response = requests.get(url, params=params)

	if response.status_code == 200:
		file_path = os.path.join(species_dir, f"{genome_id}.zip")
		with open(file_path, "wb") as f:
			f.write(response.content)
		print(f"Download concluído: {file_path}")

		# Extraindo todos os arquivos
		print("Extraindo .fna...")
		caminho_zip = f"{species_dir}/{genome_id}.zip"
		with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
			zip_ref.extractall(f"{species_dir}/zip/")

		# Separando todos os cromossomos em arquivos .fasta
		fna_path = f"{species_dir}/zip/ncbi_dataset/data/{genome_id}/"
		arquivo_fna = os.listdir(fna_path)[0]
		split_fna_by_chromosome(f"{fna_path}/{arquivo_fna}", os.path.join("data", species_name, f"{species_name}_TER_merged.gff3"), species_dir)

		# Removendo os arquivos do zip
		shutil.rmtree(f"{species_dir}/zip/")
		os.remove(caminho_zip)
	else:
		print(f"Erro ao baixar {genome_id} (Status: {response.status_code})")
		print(f"Resposta do servidor: {response.text}")

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Uso correto: python script.py <genome_id> <species_name>")
		sys.exit(1)

	genome_id = sys.argv[1]
	species_name = sys.argv[2]

	baixar_fasta(genome_id, species_name)