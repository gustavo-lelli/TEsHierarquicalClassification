import os
import subprocess
import logging
from datetime import datetime

# Configurações
DATA_DIR = "data"
MATHFEATURE_PATH = "python3 MathFeature"
PREPROCESSING_SCRIPT = "preprocessing/preprocessing.py"
MAPPING_SCRIPT = "methods/MappingClass.py"
REPRESENTATIONS = {
	#1: "binary",
	2: "z-curve",
	3: "real",
	4: "integer",
	5: "eiip",
	6: "complex_number",
	7: "atomic_number"
}

# Configuração do sistema de logs
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler("mappings.log"),
		logging.StreamHandler()
	]
)

def check_file_valid(domain_path, seq_path):
	"""Verifica se os arquivos existem e são válidos"""
	if not os.path.exists(domain_path):
		logging.warning(f"Arquivo de domínio não encontrado: {domain_path}")
		return False
	
	if os.path.getsize(domain_path) == 0:
		logging.warning(f"Arquivo de domínio vazio: {domain_path}")
		return False
	
	if not os.path.exists(seq_path):
		logging.error(f"Sequência correspondente não encontrada: {seq_path}")
		return False
	
	return True

def run_preprocessing(plant, seq_name):
	"""Executa um mapeamento individual"""
	seq_path = os.path.join(DATA_DIR, plant, "seq", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "mappings", "preprocessing")
	os.makedirs(output_dir, exist_ok=True)
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '.csv')}")
	command = f"{os.path.join(MATHFEATURE_PATH, PREPROCESSING_SCRIPT)} -i {seq_path} -o {output_file}"
	
	try:
		subprocess.run(command, shell=True, check=True)
		logging.info(f"SUCESSO: {plant}/{seq_name} -> preprocessing")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA: {plant}/{seq_name} -> preprocessing | Erro: {str(e)}")
		return False
	
def run_mapping(plant, seq_name, representation_num):
	"""Executa o mapeamento usando a sintaxe do MappingClass.py"""
	seq_path = os.path.join(DATA_DIR, plant, "seq", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "mappings", REPRESENTATIONS[representation_num])
	os.makedirs(output_dir, exist_ok=True)

	in_name = "map.in"
	with open(in_name, "w") as f:
		f.write(f"{seq_path}\n")
		f.write(f"{REPRESENTATIONS[representation_num]}\n")
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_{REPRESENTATIONS[representation_num]}.csv")
	
	cmd = f"{os.path.join(MATHFEATURE_PATH, MAPPING_SCRIPT)} -n 1 -o {output_file} -r {str(representation_num)} < {in_name}"
	
	try:
		result = subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			raise ValueError("Arquivo de saída não foi criado")
			
		logging.info(f"SUCESSO: {plant}/{seq_name} -> {REPRESENTATIONS[representation_num]}")
		return True
		
	except subprocess.TimeoutExpired:
		logging.error(f"TIMEOUT: {plant}/{seq_name} -> {REPRESENTATIONS[representation_num]}")
		return False
		
	except Exception as e:
		logging.error(f"FALHA: {plant}/{seq_name} -> {REPRESENTATIONS[representation_num]} | Erro: {str(e)}")
		if os.path.exists(output_file):
			os.remove(output_file)
		return False

if __name__ == "__main__":
	"""Processa todas as sequências válidas"""
	start_time = datetime.now()
	logging.info(f"Iniciando processamento em {start_time}")
	
	stats = {
		'total_sequences': 0,
		'processed': 0,
		'skipped': 0,
		'failed': 0
	}

	for plant in sorted(os.listdir(DATA_DIR)):
		plant_dir = os.path.join(DATA_DIR, plant)
		domains_dir = os.path.join(plant_dir, "domains")
		sequences_dir = os.path.join(plant_dir, "seq")
		
		if not os.path.exists(domains_dir) or not os.path.exists(sequences_dir):
			continue

		for domain_file in sorted(os.listdir(domains_dir)):
			if not domain_file.endswith('.tsv'):
				continue

			stats['total_sequences'] += 1
			domain_path = os.path.join(domains_dir, domain_file)
			seq_name = domain_file.replace('.tsv', '.fasta')
			seq_path = os.path.join(sequences_dir, seq_name)

			if not check_file_valid(domain_path, seq_path):
				stats['skipped'] += 1
				continue

			# Processa todos os mapeamentos para esta sequência
			seq_success = True
			if run_preprocessing(plant, seq_name):
				for num, name in REPRESENTATIONS.items():
					if not run_mapping(plant, seq_name, num):
						seq_success = False
						stats['failed'] += 1
			else:
				seq_success = False
				stats['failed'] += 1
			
			if seq_success:
				stats['processed'] += 1

	# Relatório final
	end_time = datetime.now()
	duration = end_time - start_time
	
	logging.info("\n=== RESUMO FINAL ===")
	logging.info(f"Tempo total: {duration}")
	logging.info(f"Sequências encontradas: {stats['total_sequences']}")
	logging.info(f"Sequências processadas: {stats['processed']}")
	logging.info(f"Sequências ignoradas: {stats['skipped']}")
	logging.info(f"Mapeamentos com falha: {stats['failed']}")
	logging.info(f"Arquivo de log salvo em: mappings.log")