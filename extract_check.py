import os

# Pasta raiz onde estão as pastas das espécies
data_folder = "data"

# Arquivo de saída para o relatório
output_file = "status_report.txt"

# Dicionário para armazenar o status de cada espécie
species_status = {}

# Dicionário para armazenar o status geral
general_status = {
	"processed": 0,
	"pending": 0,
	"percentage_processed": 0,
	"empty": 0,
	"not_empty": 0,
	"percentage_empty": 0,
}

# Percorre todas as pastas de espécies
for species_name in sorted(os.listdir(data_folder)):
	species_folder = os.path.join(data_folder, species_name)

	# Verifica se é uma pasta
	if os.path.isdir(species_folder):
		sequences_folder = os.path.join(species_folder, "seq")
		domains_folder = os.path.join(species_folder, "domains")

		# Verifica se as pastas de sequências e domínios existem
		if os.path.exists(sequences_folder) and os.path.exists(domains_folder):
			# Conta a quantidade de arquivos .fasta na pasta de sequências
			total_sequences = len([f for f in os.listdir(sequences_folder) if f.endswith('.fasta')])

			# Conta a quantidade de arquivos .tsv na pasta de domínios
			processed_sequences = len([f for f in os.listdir(domains_folder) if f.endswith('.tsv')])

			# Calcula a quantidade de sequências pendentes
			pending_sequences = total_sequences - processed_sequences

			# Calcula a porcentagem de sequências processadas
			percentage_processed = (processed_sequences / total_sequences) * 100 if total_sequences > 0 else 0

			# Verifica se os arquivos .tsv estão vazios ou não
			empty_files = 0
			not_empty_files = 0			
			for file in os.listdir(domains_folder):
				if file.endswith('.tsv'):
					full_path = os.path.join(domains_folder, file)

				# Verifica se o arquivo está vazio
				if os.path.getsize(full_path) == 0:
					empty_files += 1
				else:
					not_empty_files += 1
			
			percentage_empty = (empty_files / (empty_files + not_empty_files)) * 100 if (empty_files + not_empty_files) > 0 else 0

			# Armazena o status da espécie
			species_status[species_name] = {
				"processed": processed_sequences,
				"pending": pending_sequences,
				"percentage_processed": percentage_processed,
				"empty": empty_files,
				"not_empty": not_empty_files,
				"percentage_empty": percentage_empty
			}

			# Atualiza o status geral
			general_status["processed"] += processed_sequences
			general_status["pending"] += pending_sequences
			general_status["empty"] += empty_files
			general_status["not_empty"] += not_empty_files


# Calcula a porcentagem geral
total_sequences_general = general_status["processed"] + general_status["pending"]
general_status["percentage_processed"] = (general_status["processed"] / total_sequences_general) * 100 if total_sequences_general > 0 else 0
total_sequences_domains = general_status["empty"] + general_status["not_empty"]
general_status["percentage_empty"] = (general_status["empty"] / total_sequences_domains) * 100 if total_sequences_domains > 0 else 0

# Escreve o relatório no arquivo de saída
with open(output_file, "w") as f:
	f.write("Relatório de Processamento de Sequências por Espécie:\n")
	f.write("=" * 50 + "\n")
	for species, status in species_status.items():
		f.write(f"Espécie: {species}\n")
		f.write(f"Sequências processadas: {status['processed']}\n")
		f.write(f"Sequências pendentes: {status['pending']}\n")
		f.write(f"Porcentagem processada: {status['percentage_processed']:.2f}%\n")
		f.write(f"Arquivos vazios: {status['empty']}\n")
		f.write(f"Arquivos não vazios: {status['not_empty']}\n")
		f.write(f"Porcentagem de arquivos vazios: {status['percentage_empty']:.2f}%\n")
		f.write("-" * 50 + "\n")

	f.write("Geral:\n")
	f.write(f"Sequências processadas: {general_status['processed']}\n")
	f.write(f"Sequências pendentes: {general_status['pending']}\n")
	f.write(f"Porcentagem processada: {general_status['percentage_processed']:.2f}%\n")
	f.write(f"Arquivos vazios: {general_status['empty']}\n")
	f.write(f"Arquivos não vazios: {general_status['not_empty']}\n")
	f.write(f"Porcentagem de arquivos vazios: {general_status['percentage_empty']:.2f}%\n")
	f.write("-" * 50 + "\n")

print(f"Relatório gerado com sucesso em {output_file}")