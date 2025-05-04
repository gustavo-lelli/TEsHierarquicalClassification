import os
import subprocess
import logging
from multiprocessing import Pool, cpu_count
import gc
from datetime import datetime

# Configurações
DATA_DIR = "data"
MATHFEATURE_PATH = "MathFeature"
PREPROCESSING_SCRIPT = f"{MATHFEATURE_PATH}/preprocessing/preprocessing.py"
OPERATIONS_DIR = "methods"
SCRIPTS = {
	"mapping": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/MappingClass.py",
	"fourier": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/FourierClass.py",
	"chaos": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/ChaosGameTheory.py",
	"entropy": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/EntropyClass.py",
	"tsallis": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/TsallisEntropy.py",
	"complex_networks": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/ComplexNetworksClass-v2.py",
	"k-mer": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/ExtractionTechniques.py",
	"anf": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/AccumulatedNucleotideFrequency.py",
	"orf": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/CodingClass.py",
	"fickett_score": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/FickettScore.py",
	"pse-knc": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/PseKNC.py", # Não implementado
	"kgap": f"{MATHFEATURE_PATH}/{OPERATIONS_DIR}/Kgap.py", # Não implementado

}

# Representações numéricas
NUMERICAL_REPRESENTATIONS = {
	# 1: "binary",
	2: "z-curve",
	3: "real",
	4: "integer",
	5: "eiip",
	6: "complex_number",
	7: "atomic_number"
}

# Abordagens de Chaos Game
CHAOS_APPROACHES = {
	1: "classic",
	2: "frequency",
	3: "signal_classic",
	4: "signal_frequency"
}

# Tipos de Entropia
ENTROPY_TYPES = {
	1: "shannon",
	2: "tsallis"
}

# Tipos de ANF
ANF_TYPES = {
	1: "classic",
	2: "fourier",
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

def is_already_processed(plant, seq_name, operation=None, representation_num=None):
	"""Verifica se o processamento já foi realizado"""
	base_name = seq_name.replace('.fasta', '')
	
	# Verifica pré-processamento
	if operation is None:
		preprocessed_file = os.path.join(DATA_DIR, plant, "preprocessing", f"{base_name}.fasta")
		return os.path.exists(preprocessed_file)
	
	# Determina o diretório de saída baseado na operação
	if operation == "mapping":
		output_dir = os.path.join(DATA_DIR, plant, "mappings", NUMERICAL_REPRESENTATIONS[representation_num])
		output_file = os.path.join(output_dir, f"{base_name}_{NUMERICAL_REPRESENTATIONS[representation_num]}.csv")
	elif operation == "chaos":
		output_dir = os.path.join(DATA_DIR, plant, "chaos", CHAOS_APPROACHES[representation_num])
		output_file = os.path.join(output_dir, f"{base_name}_{CHAOS_APPROACHES[representation_num]}.csv")
	elif operation == "fourier":
		output_dir = os.path.join(DATA_DIR, plant, "fourier", NUMERICAL_REPRESENTATIONS[representation_num])
		output_file = os.path.join(output_dir, f"{base_name}_{NUMERICAL_REPRESENTATIONS[representation_num]}.csv")
	elif operation == "entropy":
		output_dir = os.path.join(DATA_DIR, plant, "entropy", ENTROPY_TYPES[representation_num])
		output_file = os.path.join(output_dir, f"{base_name}_{ENTROPY_TYPES[representation_num]}.csv")
	elif operation == "complex_networks":
		output_dir = os.path.join(DATA_DIR, plant, "complex_networks")
		output_file = os.path.join(output_dir, f"{base_name}_complex_networks.csv")
	elif operation == "k-mer":
		output_dir = os.path.join(DATA_DIR, plant, "k-mer")
		output_file = os.path.join(output_dir, f"{base_name}_k-mer.csv")
	elif operation == "anf":
		output_dir = os.path.join(DATA_DIR, plant, "anf", ANF_TYPES[representation_num])
		output_file = os.path.join(output_dir, f"{base_name}_{ANF_TYPES[representation_num]}.csv")
	elif operation == "orf":
		output_dir = os.path.join(DATA_DIR, plant, "orf")
		output_file = os.path.join(output_dir, f"{base_name}_orf.csv")
	elif operation == "fickett_score":
		output_dir = os.path.join(DATA_DIR, plant, "fickett_score")
		output_file = os.path.join(output_dir, f"{base_name}_fickett_score.csv")
	else:
		return False
	
	return os.path.exists(output_file)

def run_preprocessing(plant, seq_name):
	"""Executa o pré-processamento se necessário"""
	if is_already_processed(plant, seq_name):
		logging.info(f"PRÉ-PROCESSAMENTO JÁ EXISTE: {plant}/{seq_name}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "seq", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "preprocessing")
	os.makedirs(output_dir, exist_ok=True)
	
	output_file = os.path.join(output_dir, seq_name)
	command = f"python3 {PREPROCESSING_SCRIPT} -i {seq_path} -o {output_file}"
	
	try:
		subprocess.run(command, shell=True, check=True)
		logging.info(f"SUCESSO PRÉ-PROCESSAMENTO: {plant}/{seq_name}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA PRÉ-PROCESSAMENTO: {plant}/{seq_name} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória

def run_numerical_mapping(plant, seq_name, representation_num):
	"""Executa o mapeamento se necessário"""
	if is_already_processed(plant, seq_name, "mapping", representation_num):
		logging.info(f"MAPEAMENTO JÁ EXISTE: {plant}/{seq_name} -> {NUMERICAL_REPRESENTATIONS[representation_num]}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "mappings", NUMERICAL_REPRESENTATIONS[representation_num])
	os.makedirs(output_dir, exist_ok=True)

	in_name = f"map_{seq_name}.in"
	with open(in_name, "w") as f:
		f.write(f"{seq_path}\n")
		f.write(f"{NUMERICAL_REPRESENTATIONS[representation_num]}\n")
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_{NUMERICAL_REPRESENTATIONS[representation_num]}.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["mapping"],
		"-n", "1",
		"-o", output_file,
		"-r", str(representation_num),
		"<", in_name
	])

	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA MAPEAMENTO: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO MAPEAMENTO: {plant}/{seq_name} -> {NUMERICAL_REPRESENTATIONS[representation_num]}")
		return True
	except Exception as e:
		logging.error(f"FALHA MAPEAMENTO: {plant}/{seq_name} -> {NUMERICAL_REPRESENTATIONS[representation_num]} | Erro: {str(e)}")
		if os.path.exists(output_file):
			os.remove(output_file)
		return False
	finally:
		gc.collect()  # Liberar memória
		os.remove(in_name)  # Remove o arquivo de entrada


def run_chaos_mapping(plant, seq_name, approach_num):
	"""Executa o Chaos Game Theory"""
	if is_already_processed(plant, seq_name, "chaos", approach_num):
		logging.info(f"CHAOS JÁ EXISTE: {plant}/{seq_name} -> {CHAOS_APPROACHES[approach_num]}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "chaos", CHAOS_APPROACHES[approach_num])
	os.makedirs(output_dir, exist_ok=True)
	
	in_name = f"chaos_{seq_name}.in"
	with open(in_name, "w") as f:
		f.write(f"{seq_path}\n")
		f.write(f"{CHAOS_APPROACHES[approach_num]}\n")
		if approach_num % 2 == 0:
			f.write("4\n")
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_{CHAOS_APPROACHES[approach_num]}.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["chaos"],
		"-n", "1",
		"-o", output_file,
		"-r", str(approach_num),
		"<", in_name
	])
	
	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA CHAOS: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO CHAOS: {plant}/{seq_name} -> {CHAOS_APPROACHES[approach_num]}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA CHAOS: {plant}/{seq_name} -> {CHAOS_APPROACHES[approach_num]} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória
		os.remove(in_name)  # Remove o arquivo de entrada

def run_fourier_analysis(plant, seq_name, representation_num):
	"""Executa análise de Fourier"""
	if is_already_processed(plant, seq_name, "fourier", representation_num):
		logging.info(f"FOURIER JÁ EXISTE: {plant}/{seq_name}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "fourier", NUMERICAL_REPRESENTATIONS[representation_num])
	os.makedirs(output_dir, exist_ok=True)
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_{NUMERICAL_REPRESENTATIONS[representation_num]}.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["fourier"],
		"-i", seq_path,
		"-o", output_file,
		"-l", NUMERICAL_REPRESENTATIONS[representation_num],
		"-r", str(representation_num)
	])
	
	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA FOURIER: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO FOURIER: {plant}/{seq_name}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA FOURIER: {plant}/{seq_name} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória

def run_entropy_analysis(plant, seq_name, entropy_type):
	"""Executa análise de Entropia"""
	if is_already_processed(plant, seq_name, "entropy", entropy_type):
		logging.info(f"ENTROPIA JÁ EXISTE: {plant}/{seq_name} -> {ENTROPY_TYPES[entropy_type]}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "entropy", ENTROPY_TYPES[entropy_type])
	os.makedirs(output_dir, exist_ok=True)
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_{ENTROPY_TYPES[entropy_type]}.csv")
	
	if entropy_type == 1:  # Shannon
		cmd = ' '.join([
			"python3",
			SCRIPTS["entropy"],
			"-i", seq_path,
			"-o", output_file,
			"-l", "shannon",
			"-k", "4",  # 1-mer e 2-mer
			"-e", "Shannon"
		])
	else:  # Tsallis
		cmd = ' '.join([
			"python3",
			SCRIPTS["tsallis"],
			"-i", seq_path,
			"-o", output_file,
			"-l", "tsallis",
			"-k", "4",
			"-q", "2.5"  # Parâmetro q padrão
		])
	
	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA ENTROPIA: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO ENTROPIA: {plant}/{seq_name} -> {ENTROPY_TYPES[entropy_type]}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA ENTROPIA: {plant}/{seq_name} -> {ENTROPY_TYPES[entropy_type]} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória

def run_complex_networks(plant, seq_name):
	"""Executa análise de Redes Complexas"""
	if is_already_processed(plant, seq_name, "complex_networks"):
		logging.info(f"REDES COMPLEXAS JÁ EXISTEM: {plant}/{seq_name}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "complex_networks")
	os.makedirs(output_dir, exist_ok=True)
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_complex_networks.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["complex_networks"],
		"-i", seq_path,
		"-o", output_file,
		"-l", "complex_networks",
		"-k", "4"  # k-mer 2 e 3
	])
	
	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA REDES COMPLEXAS: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO REDES COMPLEXAS: {plant}/{seq_name}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA REDES COMPLEXAS: {plant}/{seq_name} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória

def run_k_mer(plant, seq_name):
	"""Executa análise de k-mer"""
	if is_already_processed(plant, seq_name, "k-mer"):
		logging.info(f"K-MER JÁ EXISTE: {plant}/{seq_name}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "k-mer")
	os.makedirs(output_dir, exist_ok=True)

	in_name = f"kmer_{seq_name}.in"
	with open(in_name, "w") as f:
		f.write("6\n")
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_k-mer.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["k-mer"],
		"-i", seq_path,
		"-o", output_file,
		"-l", "6-mer",
		"-t", "kmer",
		"-seq", "1", # DNA
		"<", in_name
	])

	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)

		if not os.path.exists(output_file):
			logging.error(f"FALHA K-MER: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO K-MER: {plant}/{seq_name}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA K-MER: {plant}/{seq_name} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória
		os.remove(in_name)  # Remove o arquivo de entrada

def run_accumulated_nucleotide_frequency(plant, seq_name, representation_num):
	"""Executa analise de ANF"""
	if is_already_processed(plant, seq_name, "anf", representation_num):
		logging.info(f"ANF JÁ EXISTE: {plant}/{seq_name} -> {ANF_TYPES[representation_num]}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "anf", ANF_TYPES[representation_num])
	os.makedirs(output_dir, exist_ok=True)

	in_name = f"anf_{seq_name}.in"
	with open(in_name, "w") as f:
		f.write(f"{seq_path}\n")
		f.write(f"{ANF_TYPES[representation_num]}\n")
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_{ANF_TYPES[representation_num]}.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["anf"],
		"-n", "1",
		"-o", output_file,
		"-r", str(representation_num),
		"<", in_name
	])

	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA ANF: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO ANF: {plant}/{seq_name} -> {ANF_TYPES[representation_num]}")
		return True
	except Exception as e:
		logging.error(f"FALHA ANF: {plant}/{seq_name} -> {ANF_TYPES[representation_num]} | Erro: {str(e)}")
		if os.path.exists(output_file):
			os.remove(output_file)
		return False
	finally:
		gc.collect()  # Liberar memória
		os.remove(in_name)  # Remove o arquivo de entrada

def run_orf(plant, seq_name):
	"""Executa análise de ORF Description"""
	if is_already_processed(plant, seq_name, "orf"):
		logging.info(f"ORF JÁ EXISTEM: {plant}/{seq_name}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "orf")
	os.makedirs(output_dir, exist_ok=True)
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_orf.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["orf"],
		"-i", seq_path,
		"-o", output_file,
		"-l", "orf",
	])
	
	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA ORF: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO ORF: {plant}/{seq_name}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA ORF: {plant}/{seq_name} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória

def run_fickett_score(plant, seq_name):
	"""Executa análise de fickett score"""
	if is_already_processed(plant, seq_name, "fickett_score"):
		logging.info(f"FICKETT SCORE JÁ EXISTEM: {plant}/{seq_name}")
		return True
		
	seq_path = os.path.join(DATA_DIR, plant, "preprocessing", seq_name)
	output_dir = os.path.join(DATA_DIR, plant, "fickett_score")
	os.makedirs(output_dir, exist_ok=True)
	
	output_file = os.path.join(output_dir, f"{seq_name.replace('.fasta', '')}_fickett_score.csv")
	cmd = ' '.join([
		"python3",
		SCRIPTS["fickett_score"],
		"-i", seq_path,
		"-o", output_file,
		"-l", "fickett_score",
		"-seq", "1", # DNA
	])
	
	try:
		subprocess.run(
			cmd,
			shell=True,
			check=True,
			timeout=600,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		
		if not os.path.exists(output_file):
			logging.error(f"FALHA FICKETT SCORE: {plant}/{seq_name} | Erro: Arquivo de saída não foi criado")
			return False
			
		logging.info(f"SUCESSO FICKETT SCORE: {plant}/{seq_name}")
		return True
	except subprocess.CalledProcessError as e:
		logging.error(f"FALHA FICKETT SCORE: {plant}/{seq_name} | Erro: {str(e)}")
		return False
	finally:
		gc.collect()  # Liberar memória

def process_sequence(domain_file, plant, domains_dir, sequences_dir, stats):
	if not domain_file.endswith('.tsv'):
		return

	stats['total_sequences'] += 1
	domain_path = os.path.join(domains_dir, domain_file)
	seq_name = domain_file.replace('.tsv', '.fasta')
	seq_path = os.path.join(sequences_dir, seq_name)

	if not check_file_valid(domain_path, seq_path):
		stats['skipped'] += 1
		return
	
	# Verifica se todos os processamentos já foram feitos
	all_processed = True
	required_operations = [
		(None, None),  # Pré-processamento
	] + [
		("mapping", num) for num in NUMERICAL_REPRESENTATIONS
	] + [
		("chaos", num) for num in CHAOS_APPROACHES
	] + [
		("fourier", num) for num in NUMERICAL_REPRESENTATIONS
	] + [
		("entropy", num) for num in ENTROPY_TYPES
	] + [
		("complex_networks", None),
		("k-mer", None)
	] + [
		("anf", num) for num in ANF_TYPES
	] + [
		("orf", None),
		("fickett_score", None)
	]

	for operation, num in required_operations:
		if not is_already_processed(plant, seq_name, operation, num):
			all_processed = False
			break
	
	if all_processed:
		stats['already_processed'] += 1
		logging.info(f"TUDO PROCESSADO: {plant}/{seq_name}")
		return

	# Executa os processamentos necessários
	seq_success = True
	
	if not run_preprocessing(plant, seq_name):
		seq_success = False
		stats['failed'] += 1
	else:
		# Processa Mapeamentos Numéricos
		for num in NUMERICAL_REPRESENTATIONS:
			if not run_numerical_mapping(plant, seq_name, num):
				seq_success = False
				stats['failed'] += 1

		# Processa Chaos Game
		for approach_num in CHAOS_APPROACHES:
			if not run_chaos_mapping(plant, seq_name, approach_num):
				seq_success = False
				stats['failed'] += 1

		# Processa Fourier
		for num in NUMERICAL_REPRESENTATIONS:
			if not run_fourier_analysis(plant, seq_name, num):
				seq_success = False
				stats['failed'] += 1

		# Processa Entropias
		for entropy_type in ENTROPY_TYPES:
			if not run_entropy_analysis(plant, seq_name, entropy_type):
				seq_success = False
				stats['failed'] += 1

		# Processa Redes Complexas
		if not run_complex_networks(plant, seq_name):
			seq_success = False
			stats['failed'] += 1

		# Processa K-Mer
		if not run_k_mer(plant, seq_name):
			seq_success = False
			stats['failed'] += 1

		# Processa ANF
		for num in ANF_TYPES:
			if not run_accumulated_nucleotide_frequency(plant, seq_name, num):
				seq_success = False
				stats['failed'] += 1

		# Processa ORF
		if not run_orf(plant, seq_name):
			seq_success = False
			stats['failed'] += 1

		# Processa Fickett Score
		if not run_fickett_score(plant, seq_name):
			seq_success = False
			stats['failed'] += 1

		if seq_success:
			stats['processed'] += 1


if __name__ == "__main__":
	start_time = datetime.now()
	logging.info(f"Iniciando processamento em {start_time}")
	
	stats = {
		'total_sequences': 0,
		'processed': 0,
		'skipped': 0,
		'failed': 0,
		'already_processed': 0
	}

	for plant in sorted(os.listdir(DATA_DIR)):
		plant_dir = os.path.join(DATA_DIR, plant)
		domains_dir = os.path.join(plant_dir, "domains")
		sequences_dir = os.path.join(plant_dir, "seq")
		
		if not os.path.exists(domains_dir) or not os.path.exists(sequences_dir):
			continue

		num_processes = max(1, cpu_count() // 2)  # Usar metade dos núcleos da CPU

		# Lista para armazenar sequências que precisam ser processadas
		sequences_to_process = []

		# Processa apenas as sequências que ainda não foram processadas
		with Pool(num_processes) as pool:
			results = pool.starmap(process_sequence, [
				(domain_file, plant, domains_dir, sequences_dir, stats)
				for domain_file in sorted(os.listdir(domains_dir))
			])
			
	# Relatório final
	end_time = datetime.now()
	duration = end_time - start_time
	
	logging.info("\n=== RESUMO FINAL ===")
	logging.info(f"Tempo total: {duration}")
	logging.info(f"Sequências encontradas: {stats['total_sequences']}")
	logging.info(f"Sequências processadas agora: {stats['processed']}")
	logging.info(f"Sequências já processadas anteriormente: {stats['already_processed']}")
	logging.info(f"Sequências ignoradas: {stats['skipped']}")
	logging.info(f"Operações com falha: {stats['failed']}")
	logging.info("Arquivo de log salvo em: mappings.log")
