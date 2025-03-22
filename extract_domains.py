import subprocess
import os
import time
import gc
from multiprocessing import Pool, cpu_count
import logging
import re

Status = {
	"PROCESSING": -1,
	"WATING/ERROR": 0,
	"SUCCESS": 1
}

# Configuração de logs
logging.basicConfig(
	filename='extract_domains.log',
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)

# Função para ler o status das espécies e adicionar novas espécies com status WAITING/ERROR
def read_status(status_file, species_list):
	status = {}

	# Se o arquivo de status não existir, cria um novo com todas as espécies como não processadas (WAITING/ERROR)
	if not os.path.exists(status_file):
		with open(status_file, "w") as f:
			for species in species_list:
				f.write(f"{species}:{Status["WAITING/ERROR"]}\n")
				status[species] = Status["WAITING/ERROR"]
	else:
		# Se o arquivo existir, lê o status atual
		with open(status_file, "r") as f:
			lines = f.readlines()
			existing_species = set()
			for line in lines:
				species, state = line.strip().split(":")
				status[species] = int(state)
				existing_species.add(species)

			new_species = set(species_list) - existing_species

			if new_species:
				with open(status_file, "a") as f:
					for species in new_species:
						f.write(f"{species}:{Status["WAITING/ERROR"]}\n")
						status[species] = Status["WAITING/ERROR"]
	return status

# Função para atualizar o status de uma espécie
def update_status(status_file, species, state):
	status = {}
	if os.path.exists(status_file):
		with open(status_file, "r") as f:
			for line in f:
				s, st = line.strip().split(":")
				status[s] = int(st)

	status[species] = state
	
	with open(status_file, "w") as f:
		for s, st in status.items():
			f.write(f"{s}:{st}\n")

# Função para processar uma sequência
def process_sequence(sequence_file, sequences_folder, output_folder, interproscan_path, applications, output_format):
	# Timer para a sequência
	sequence_start_time = time.time()

	sequence_path = os.path.join(sequences_folder, sequence_file)
	output_path = os.path.join(output_folder, sequence_file.replace('.fasta', ''))

	command = [
		interproscan_path,
		"-i", sequence_path,
		"-appl", ','.join(applications),
		"-b", output_path,
		"-f", output_format
	]

	patterns_to_remove = [r'data/', r'domains/', r'\.fasta']
	regex_pattern = '|'.join(patterns_to_remove)
	output_species_log = re.sub(regex_pattern, '', output_path)

	try:
		result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)

		# Timer para o cromossomo
		sequence_end_time = time.time()
		logging.info(f"Sequência {output_species_log} processada em {sequence_end_time - sequence_start_time:.2f} segundos.")
	except subprocess.CalledProcessError as e:
		logging.error(f"Erro ao processar {output_species_log}: {e.stderr}")
	finally:
		gc.collect()  # Liberar memória

# Função para verificar se uma sequência já foi processada (arquivo .tsv existe)
def is_sequence_processed(sequence_file, domains_folder):
	sequence_name = sequence_file.replace('.fasta', '')
	tsv_file = os.path.join(domains_folder, f"{sequence_name}.tsv")
	return os.path.exists(tsv_file)

# Código principal
if __name__ == "__main__":
	species_list = sorted(os.listdir("data"))
	data_folder = "data"
	interproscan_path = "./InterProScan/interproscan-5.73-104.0/interproscan.sh"
	applications = ["PROSITEPATTERNS", "PROSITEPROFILES", "CDD", "PRINTS", "Pfam"]
	output_format = "tsv"

	for species_name in species_list:
		species_folder = os.path.join(data_folder, species_name)
		os.makedirs(species_folder, exist_ok=True)

		status_file = os.path.join(data_folder, "extracted_domains.txt")
		status = read_status(status_file, species_list)

		if status.get(species_name, 0) == Status["SUCCESS"] or status.get(species_name, 0) == Status["PROCESSING"]:
			logging.info(f"Espécie {species_name} já foi ou está sendo processada. Pulando...")
			continue

		update_status(status_file, species_name, Status["PROCESSING"])
		species_folder = os.path.join(data_folder, species_name)
		os.makedirs(species_folder, exist_ok=True)

		sequences_folder = os.path.join(species_folder, "seq")
		output_folder = os.path.join(species_folder, "domains")
		os.makedirs(output_folder, exist_ok=True)

		sequences_list = sorted(os.listdir(sequences_folder))
		num_processes = max(1, cpu_count() // 2)  # Usar metade dos núcleos da CPU

		# Lista para armazenar sequências que precisam ser processadas
		sequences_to_process = []

		# Verifica quais sequências já foram processadas
		for sequence_file in sequences_list:
			if is_sequence_processed(sequence_file, output_folder):
				logging.info(f"Sequência {sequence_file} já foi processada. Pulando...")
			else:
				sequences_to_process.append(sequence_file)

		# Processa apenas as sequências que ainda não foram processadas
		with Pool(num_processes) as pool:
			results = pool.starmap(process_sequence, [
				(seq, sequences_folder, output_folder, interproscan_path, applications, output_format)
				for seq in sequences_to_process
			])

		update_status(status_file, species_name, Status["SUCCESS"])
		logging.info(f"Extração de Domínios da {species_name} Finalizado!")