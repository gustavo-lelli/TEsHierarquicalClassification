import subprocess
import os
import time

# Função para ler o status das espécies e adicionar novas espécies com status 0
def read_status(status_file, species_list):
	status = {}

	# Se o arquivo de status não existir, cria um novo com todas as espécies como não processadas (0)
	if not os.path.exists(status_file):
		with open(status_file, "w") as f:
			for species in species_list:
				f.write(f"{species}:0\n")
				status[species] = 0
	else:
		# Se o arquivo existir, lê o status atual
		with open(status_file, "r") as f:
			lines = f.readlines()
			existing_species = set()
			for line in lines:
				species, state = line.strip().split(":")
				status[species] = int(state)
				existing_species.add(species)

		# Verifica se há novas espécies que não estão no arquivo de status
		new_species = set(species_list) - existing_species
		if new_species:
			with open(status_file, "a") as f:
				for species in new_species:
					f.write(f"{species}:0\n")
					status[species] = 0

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

# Lista de todas as espécies na pasta "data"
species_list = sorted(os.listdir("data"))

data_folder = "data"
# Caminho para o script do InterProScan
interproscan_path = "./InterProScan/interproscan-5.73-104.0/interproscan.sh"

for species_name in species_list:
	if species_name == "extracted_domains.txt":
		print("Extração de Domínios Finalizado!")
		continue

	# Caminho do arquivo de controle
	status_file = os.path.join(data_folder, "extracted_domains.txt")

	# Ler o status atual e adicionar novas espécies, se necessário
	status = read_status(status_file, species_list)

	# Verificar se a espécie já foi processada
	if status.get(species_name, 0) == 1 or status.get(species_name, 0) == -1:
		print(f"Espécie {species_name} já foi ou está sendo processada. Pulando...")
		continue

	# Atualizar o status da espécie para "processando"
	update_status(status_file, species_name, -1)

	# Timer para a espécie
	species_start_time = time.time()

	species_folder = os.path.join(data_folder, species_name)
	os.makedirs(species_folder, exist_ok=True)

	sequences_folder = os.path.join(species_folder, "seq")
	output_folder = os.path.join(species_folder, "domains")
	os.makedirs(output_folder, exist_ok=True)

	# Lista de todas as espécies na pasta "data"
	sequences_list = sorted(os.listdir(sequences_folder))
	
	# Processar as sequências
	for sequence_file in sequences_list:
		# Caminho do arquivo de controle
		status_seq_file = os.path.join(species_folder, "extracted_domains.txt")
		os.makedirs(species_folder, exist_ok=True)

		# Ler o status atual e adicionar novas espécies, se necessário
		status_seq = read_status(status_seq_file, sequences_list)

		# Verificar se a sequência já foi processada
		if status_seq.get(sequence_file, 0) == 1 or status_seq.get(sequence_file, 0) == -1:
			print(f"Sequência {species_name}/{sequence_file} já foi ou está sendo processada. Pulando...")
			continue

		# Atualizar o status da sequência para "processando"
		update_status(status_seq_file, sequence_file, -1)

		# Timer para a sequência
		sequence_start_time = time.time()

		sequence_path = os.path.join(sequences_folder, sequence_file)

		# Caminho para o diretório de saída
		output_path = os.path.join(output_folder, sequence_file.replace('.fasta', ''))

		# Formato de saída
		output_format = "tsv"

		# Construindo o comando
		command = [interproscan_path, "-i", sequence_path, "-b", output_path, "-f", output_format]

		# Executando o comando
		try:
			result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)
			print("Saída do comando:")
			print(result.stdout)

			# Timer para o cromossomo
			sequence_end_time = time.time()
			print(f"Sequência {species_name}/{sequence_file.replace('.fasta', '')} processado em {sequence_end_time - sequence_start_time:.2f} segundos.")

			# Atualizar o status da sequência para "processada"
			update_status(status_seq_file, sequence_file, 1)
		except subprocess.CalledProcessError as e:
			print("Erro ao executar o comando:")
			print(e.stderr)

			# Atualizar o status da sequência para "erro"
			update_status(status_seq_file, sequence_file, 0)

	# Atualizar o status da espécie para "processada"
	update_status(status_file, species_name, 1)