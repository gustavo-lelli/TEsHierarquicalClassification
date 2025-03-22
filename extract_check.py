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
	"percentage": 0
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

			# Armazena o status da espécie
			species_status[species_name] = {
				"processed": processed_sequences,
				"pending": pending_sequences,
				"percentage": percentage_processed
			}

			# Atualiza o status geral
			general_status["processed"] += processed_sequences
			general_status["pending"] += pending_sequences

# Calcula a porcentagem geral
total_sequences_general = general_status["processed"] + general_status["pending"]
general_status["percentage"] = (general_status["processed"] / total_sequences_general) * 100 if total_sequences_general > 0 else 0

# Escreve o relatório no arquivo de saída
with open(output_file, "w") as f:
	f.write("Relatório de Processamento de Sequências por Espécie:\n")
	f.write("=" * 50 + "\n")
	for species, status in species_status.items():
		f.write(f"Espécie: {species}\n")
		f.write(f"Sequências processadas: {status['processed']}\n")
		f.write(f"Sequências pendentes: {status['pending']}\n")
		f.write(f"Porcentagem processada: {status['percentage']:.2f}%\n")
		f.write("-" * 50 + "\n")

	f.write("Geral:\n")
	f.write(f"Sequências processadas: {general_status['processed']}\n")
	f.write(f"Sequências pendentes: {general_status['pending']}\n")
	f.write(f"Porcentagem processada: {general_status['percentage']:.2f}%\n")
	f.write("-" * 50 + "\n")

print(f"Relatório gerado com sucesso em {output_file}")