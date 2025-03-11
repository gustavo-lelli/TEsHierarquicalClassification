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

	# Verifica se é uma pasta e se contém o arquivo extracted_domains.txt
	if os.path.isdir(species_folder):
		status_file = os.path.join(species_folder, "extracted_domains.txt")

		if os.path.exists(status_file):
			# Inicializa os contadores para a espécie
			processed = 0
			pending = 0

			# Lê o arquivo extracted_domains.txt
			with open(status_file, "r") as f:
				for line in f:
					sequence, status = line.strip().split(":")
					if status == "1":
						processed += 1
					else:
						pending += 1

			# Armazena o status da espécie
			species_status[species_name] = {
				"processed": processed,
				"pending": pending,
				"percentage": processed / (processed + pending) * 100
			}

			# Atualiza o status geral
			general_status["processed"] += processed
			general_status["pending"] += pending

# Calcula a porcentagem geral
general_status["percentage"] = general_status["processed"] / (general_status["processed"] + general_status["pending"]) * 100

# Escreve o relatório no arquivo de saída
with open(output_file, "w") as f:
	f.write("Relatório de Processamento de Sequências por Espécie:\n")
	f.write("=" * 50 + "\n")
	for species, status in species_status.items():
		f.write(f"Espécie: {species}\n")
		f.write(f"Sequências processadas: {status['processed']}\n")
		f.write(f"Sequências pendentes: {status['pending']}\n")
		f.write(f"Porcentagem processada: {status['percentage']}%\n")
		f.write("-" * 50 + "\n")

	f.write("Geral:\n")
	f.write(f"Sequências processadas: {general_status['processed']}\n")
	f.write(f"Sequências pendentes: {general_status['pending']}\n")
	f.write(f"Porcentagem processada: {general_status['percentage']}%\n")
	f.write("-" * 50 + "\n")

print(f"Relatório gerado com sucesso em {output_file}")