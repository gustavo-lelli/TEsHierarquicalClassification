import os
import pandas as pd
import gc
import time

# Função para ler o status das espécies e adicionar novas espécies com status 0
def read_status(species_list):
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
def update_status(species, state):
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
for species_name in species_list:
	if species_name == "status.txt":
		print("Processamento Finalizado!")
		continue

	# Caminho do arquivo de controle
	status_file = os.path.join("data", "status.txt")

	# Ler o status atual e adicionar novas espécies, se necessário
	status = read_status(species_list)

	# Verificar se a espécie já foi processada
	if status.get(species_name, 0) == 1 or status.get(species_name, 0) == -1:
		print(f"Espécie {species_name} já foi ou está sendo processada. Pulando...")
		continue

	# Atualizar o status da espécie para "processando"
	update_status(species_name, -1)

	# Timer para a espécie
	species_start_time = time.time()

	fasta_folder = os.path.join(data_folder, species_name, "fasta")
	output_folder = os.path.join(data_folder, species_name, "seq")

	os.makedirs(output_folder, exist_ok=True)

	# Definir os nomes das colunas do arquivo GFF3
	column_names = ["Chr", "SourceAnnotation", "COS", "Start", "End", "Score", "Strand", "Phase", "Attributes"]

	# Lista para armazenar os dados do novo arquivo
	data = []

	gff3_path = os.path.join(data_folder, species_name, f"{species_name}_TER_merged.gff3")
	try:
		chunk_size = 10000  # Ajuste conforme necessário
		chunks = pd.read_csv(gff3_path, sep='\t', comment='#', header=None, names=column_names, chunksize=chunk_size)

		df_list = []
		for chunk in chunks:
			chunk["Start"] = chunk["Start"].astype(int)
			chunk["End"] = chunk["End"].astype(int)
			df_list.append(chunk)

		# Concatenar todos os chunks em um único DataFrame
		df = pd.concat(df_list)
		df_sorted = df.sort_values(by=['Chr']).reset_index(drop=True)

	except FileNotFoundError:
		print(f"Erro: Arquivo {gff3_path} não encontrado!")
		continue
	except Exception as e:
		print(f"Erro ao processar {gff3_path}: {e}")
		continue

	# Processar os arquivos FASTA
	for fasta_file in sorted(os.listdir(fasta_folder)):
		# Timer para o cromossomo
		chromosome_start_time = time.time()

		fasta_path = os.path.join(fasta_folder, fasta_file)

		with open(fasta_path, "r") as f:
			fasta_data = f.readlines()

		# Ignorar a primeira linha e juntar todas as sequências
		full_sequence = "".join(line.strip() for line in fasta_data[1:])

		# Gerar os arquivos segmentados
		for row in df_sorted.itertuples(index=False):
			if fasta_file.replace(".fasta", "") != row.Chr:
				continue

			chr_name, start, end = row.Chr, row.Start, row.End

			if start > len(full_sequence) or end > len(full_sequence):
  				continue

			subseq = full_sequence[start-1:end]
			output_path = os.path.join(output_folder, f"{chr_name}_{start}_{end}.fasta")

			with open(output_path, "w") as out_f:
				out_f.write(f">{chr_name}_{start}_{end}\n{subseq}\n")

			# Liberar memória imediatamente após o uso
			del subseq

		# Liberar memória após processar o arquivo FASTA
		del full_sequence
		gc.collect()

		# Timer para o cromossomo
		chromosome_end_time = time.time()
		print(f"Cromossomo {species_name}/{fasta_file.replace('.fasta', '')} processado em {chromosome_end_time - chromosome_start_time:.2f} segundos.")
		
	# Liberar memória após processar a espécie
	del df, df_sorted
	gc.collect()

	# Timer para a espécie
	species_end_time = time.time()
	print(f"Espécie {species_name} processada em {species_end_time - species_start_time:.2f} segundos.\n")

	# Atualizar o status da espécie para "processada"
	update_status(species_name, 1)