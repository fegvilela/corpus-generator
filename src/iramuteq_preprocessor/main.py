import PyPDF2
import re
import os
from unidecode import unidecode
from collections import defaultdict
from pathlib import Path
from datetime import datetime


def detect_and_remove_header(pages_text):
    """
    Detecta e remove cabeçalhos comuns em todas as páginas
    Retorna uma lista com os textos das páginas sem os cabeçalhos
    """
    if len(pages_text) < 2:
        return pages_text

    # Pega as primeiras linhas de cada página
    first_lines = []
    for page_text in pages_text:
        lines = page_text.split("\n")
        if lines:
            first_lines.append(lines[0].strip())

    # Encontra o prefixo comum entre as primeiras linhas
    common_prefix = os.path.commonprefix(first_lines)
    if (
        len(common_prefix) > 20
    ):  # Considera como cabeçalho se tiver mais de 20 caracteres
        header = common_prefix
    # Verifica se a primeira linha se repete em todas as páginas
    elif all(line == first_lines[0] for line in first_lines):
        header = first_lines[0]
    else:
        return pages_text

    # Remove o cabeçalho de cada página
    clean_pages = []
    for page_text in pages_text:
        lines = page_text.split("\n")
        if lines and lines[0].strip() == header:
            clean_pages.append("\n".join(lines[1:]))
        else:
            clean_pages.append(page_text)

    return clean_pages


def pdf_to_structured_text(pdf_path):
    """
    Extrai texto de um arquivo PDF com estrutura reconhecida
    Retorna um dicionário com: {'pages': [], 'titles': [], 'tables': [], 'figures': []}
    """
    result = {
        "pages": [],
        "titles": [],
        "tables": [],
        "figures": [],
        "metadata": defaultdict(list),
    }

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        # Extrair metadados básicos
        metadata = reader.metadata
        if metadata:
            result["metadata"]["title"] = metadata.get("/Title", "")
            result["metadata"]["author"] = metadata.get("/Author", "")
            result["metadata"]["subject"] = metadata.get("/Subject", "")

        # Primeiro extrai todo o texto para detectar cabeçalhos comuns
        all_pages_text = [page.extract_text() for page in reader.pages]
        clean_pages_text = detect_and_remove_header(all_pages_text)

        for page_num, (page, page_text) in enumerate(
            zip(reader.pages, clean_pages_text), 1
        ):
            # Processar a página para identificar elementos
            page_data = {
                "page_number": page_num,
                "content": page_text,
                "titles": [],
                "paragraphs": [],
                "tables": False,  # Placeholder - análise mais avançada necessária
                "figures": False,  # Placeholder - análise mais avançada necessária
            }

            # Identificar títulos (heurística simples - linhas com poucas palavras em caixa alta)
            lines = page_text.split("\n")
            for line in lines:
                clean_line = line.strip()
                words = clean_line.split()

                # Heurística para título
                if 1 <= len(words) <= 5 and clean_line.isupper():
                    page_data["titles"].append(clean_line)
                    result["titles"].append({"text": clean_line, "page": page_num})

            # Identificar parágrafos
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            page_data["paragraphs"] = paragraphs

            result["pages"].append(page_data)

    return result


def convert_numbers_to_words(text: str) -> str:
    """
    Converte números em algarismos para sua forma por extenso.
    Ex: "2013" → "dois mil e treze"; "70" → "setenta"
    """
    # Dicionários para conversão
    units = [
        "zero",
        "um",
        "dois",
        "três",
        "quatro",
        "cinco",
        "seis",
        "sete",
        "oito",
        "nove",
    ]

    teens = [
        "dez",
        "onze",
        "doze",
        "treze",
        "quatorze",
        "quinze",
        "dezesseis",
        "dezessete",
        "dezoito",
        "dezenove",
    ]

    tens = [
        "",
        "",
        "vinte",
        "trinta",
        "quarenta",
        "cinquenta",
        "sessenta",
        "setenta",
        "oitenta",
        "noventa",
    ]

    hundreds = [
        "",
        "cento",
        "duzentos",
        "trezentos",
        "quatrocentos",
        "quinhentos",
        "seiscentos",
        "setecentos",
        "oitocentos",
        "novecentos",
    ]

    def number_to_words(n: int) -> str:
        if n == 0:
            return units[0]

        if n == 100:
            return "cem"

        if n < 10:
            return units[n]

        if 10 <= n < 20:
            return teens[n - 10]

        if 20 <= n < 100:
            ten, unit = divmod(n, 10)
            return tens[ten] + (f" e {units[unit]}" if unit != 0 else "")

        if 100 <= n < 1000:
            hundred, remainder = divmod(n, 100)
            if remainder == 0:
                return hundreds[hundred]
            return hundreds[hundred] + " e " + number_to_words(remainder)

        if 1000 <= n < 1000000:
            thousand, remainder = divmod(n, 1000)
            thousand_part = (
                "mil" if thousand == 1 else number_to_words(thousand) + " mil"
            )
            if remainder == 0:
                return thousand_part
            if remainder < 100:
                return thousand_part + " e " + number_to_words(remainder)
            return thousand_part + " " + number_to_words(remainder)

        if 1000000 <= n < 1000000000:
            million, remainder = divmod(n, 1000000)
            million_part = number_to_words(million) + (
                " milhão" if million == 1 else " milhões"
            )
            if remainder == 0:
                return million_part
            return million_part + " " + number_to_words(remainder)

        return str(n)

    def replace_number(match: re.Match) -> str:
        num_str = match.group()

        # Trata valores monetários R$ 1.500,00
        if "R$" in num_str:
            num_str = num_str.replace("R$", "").strip()
            if "," in num_str:
                int_part, dec_part = num_str.split(",")
                int_part = int_part.replace(".", "")
                dec_part = dec_part[:2].ljust(2, "0")  # Garante 2 dígitos
            else:
                int_part = num_str.replace(".", "")
                dec_part = "00"

            int_num = int(int_part)
            dec_num = int(dec_part)

            result = number_to_words(int_num) + " reais"
            if dec_num > 0:
                result += " e " + number_to_words(dec_num) + " centavos"
            return result

        # Trata porcentagens
        if "%" in num_str:
            num = int(num_str.replace("%", ""))
            return number_to_words(num) + " por cento"

        # Trata números decimais
        if "," in num_str or "." in num_str:
            sep = "," if "," in num_str else "."
            parts = num_str.split(sep)
            integer_part = int(parts[0].replace(".", ""))
            decimal_part = parts[1] if len(parts) > 1 else "0"

            # Remove zeros à direita na parte decimal
            decimal_part = decimal_part.rstrip("0")

            result = number_to_words(integer_part)
            if decimal_part:  # Só mostra vírgula se tiver parte decimal significativa
                dec_num = int(decimal_part)
                result += " vírgula " + number_to_words(dec_num)
            return result

        # Números inteiros
        num = int(num_str)
        return number_to_words(num)

    # Padrão para identificar números no texto (incluindo valores monetários)
    number_pattern = re.compile(
        r"R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|"  # Valores monetários
        r"\b\d{1,3}(?:\.\d{3})*(?:,\d+)?%?\b|"  # números com separadores
        r"\b\d+\b"  # números simples
    )

    return number_pattern.sub(replace_number, text)


def clean_text(text, preserve_accentuation=False):
    """
    Limpa e padroniza o texto com opções avançadas
    """
    # Substitui enclise por proclise
    text = enclise_para_proclise(text)

    # Escreve  números por extenso
    text = convert_numbers_to_words(text)

    # Substitui hífens entre palavras por underscore
    text = re.sub(r"(\w)-\s*(\w)", r"\1_\2", text)

    # Casos especiais de quebra de linha com hífen
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1_\2", text)

    # Remove hífens soltos (não entre palavras)
    text = re.sub(r"(?<!\w)-(?!\w)", " ", text)

    # Normaliza espaços e quebras de linha
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    # Remove caracteres especiais indevidos
    pattern = (
        r'[\'"\-\$%\*]|\.{3}'  # Remove aspas, hífen, cifrão, %, *, e reticências (...)
    )
    text = re.sub(pattern, "", text)

    # Remove acentuação
    if not preserve_accentuation:
        text = unidecode(text)

    # Remove cabeçalhos/rodapés com números de página
    text = re.sub(r"^\d+\s+|\s+\d+$", "", text, flags=re.MULTILINE)

    return text.strip()


def enclise_para_proclise(texto):
    import re

    padrao = r"(\w+?)(-[mts]e|-l[hoa]|-lhes?|-nos|-vos)(\W|\Z)"

    def ajusta_capitalizacao(texto):
        # Divide o texto em frases (separadas por .!?)
        frases = re.split(r"([.!?]\s*)", texto)
        texto_corrigido = []

        for i, frase in enumerate(frases):
            if not frase.strip():
                continue

            # Se a frase começa com pontuação (ex: ". "), a próxima frase é capitalizada
            if re.match(r"^[.!?]\s*$", frase):
                texto_corrigido.append(frase)
                continue

            # Capitaliza a primeira letra da frase e o resto em minúscula
            frase_corrigida = frase[0].upper() + frase[1:].lower()

            # Preserva maiúsculas em nomes próprios (ex: "Maria" não vira "maria")
            # (Isso é simplificado; para 100% de precisão, use NLP)
            palavras = frase_corrigida.split()
            for j, palavra in enumerate(palavras):
                if (
                    j > 0 and palavra.istitle()
                ):  # Se não é a primeira palavra e parece um nome próprio
                    palavras[j] = palavra  # Mantém a capitalização (ex: "Maria")
            frase_corrigida = " ".join(palavras)

            texto_corrigido.append(frase_corrigida)

        return "".join(texto_corrigido)

    def corrige_verbo_para_proclise(verbo):
        if verbo.endswith(("á", "é", "ê", "í", "ó", "ú")):
            verbo = verbo[:-1] + "ar"
        elif verbo.endswith("ê"):
            verbo = verbo[:-1] + "er"
        elif verbo.endswith("í"):
            verbo = verbo[:-1] + "ir"
        return verbo

    def substituir_pronome(match):
        verbo = match.group(1)
        pronome = match.group(2)
        final = match.group(3)

        pronome_sem_hifen = pronome.replace("-", "")

        if pronome_sem_hifen in ["lo", "la"]:
            pronome_proclise = pronome_sem_hifen[-1]  # "o" ou "a"
            verbo = corrige_verbo_para_proclise(verbo)
        else:
            pronome_proclise = pronome_sem_hifen

        nova_frase = f"{pronome_proclise} {verbo}{final}"

        return nova_frase

    texto_modificado = re.sub(padrao, substituir_pronome, texto, flags=re.IGNORECASE)
    texto_modificado = ajusta_capitalizacao(texto_modificado)
    return texto_modificado


def detect_sections(text):
    """
    Tenta identificar seções no texto com base em padrões
    """
    sections = []
    current_section = []

    lines = text.split("\n")
    for line in lines:
        # Padrão para identificar títulos de seção
        if re.match(
            r"^(CAP[ÍI]TULO|SEÇÃO|PARTE)\s+[IVXLCDM0-9]+", line, re.IGNORECASE
        ) or re.match(r"^[0-9]+\.\s+[A-ZÀ-Ü]", line):
            if current_section:
                sections.append("\n".join(current_section))
                current_section = []
        current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    return sections


def prepare_iramuteq_corpus(
    structured_data, output_path, doc_name="document", include_metadata=True
):
    """
    Formata o texto estruturado para o formato IRaMuTeQ com metadados avançados
    """
    with open(output_path, "w", encoding="utf-8") as f:
        # Adicionar metadados como variáveis
        if include_metadata and structured_data["metadata"]:
            for key, values in structured_data["metadata"].items():
                if values:
                    value = values[0] if isinstance(values, list) else values
                    f.write(
                        f"**** *{doc_name} *{key.lower()}={str(value).replace(' ', '_')}\n"
                    )

        # Processar cada página
        for page in structured_data["pages"]:
            # Adicionar marcação de página (opcional)
            f.write(f"**** *{doc_name}_page{page['page_number']} *type=page\n")

            # Adicionar títulos da página como segmentos especiais
            for i, title in enumerate(page["titles"], 1):
                f.write(
                    f"**** *{doc_name}_title{i}_page{page['page_number']} *type=title\n"
                )
                f.write(clean_text(title) + "\n\n")

            # Processar parágrafos
            for i, para in enumerate(page["paragraphs"], 1):
                # Tentar detectar seções dentro do parágrafo
                sections = detect_sections(para)

                for j, section in enumerate(sections, 1):
                    clean_section = clean_text(section)
                    if clean_section:
                        f.write(
                            f"**** *{doc_name}_para{i}_section{j}_page{page['page_number']} *type=paragraph\n"
                        )
                        f.write(clean_section + "\n\n")

            # Marcar tabelas e figuras (placeholders)
            if page["tables"]:
                f.write(
                    f"**** *{doc_name}_table_page{page['page_number']} *type=table\n"
                )
                f.write("[TABLE_PLACEHOLDER]\n\n")

            if page["figures"]:
                f.write(
                    f"**** *{doc_name}_figure_page{page['page_number']} *type=figure\n"
                )
                f.write("[FIGURE_PLACEHOLDER]\n\n")


def process_pdf_folder(input_folder, output_folder, preserve_accentuation=False):
    """
    Processa todos os PDFs em uma pasta com opções avançadas
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            print(f"\n🏃 Processando: {filename}")

            try:
                # Extrair dados estruturados
                structured_data = pdf_to_structured_text(pdf_path)

                # Nome do arquivo de saída
                base_name = os.path.splitext(filename)[0] + datetime.now().strftime(
                    "%Y%m%d%H%M"
                )
                output_path = os.path.join(output_folder, f"{base_name}_iramuteq.txt")

                # Preparar corpus
                prepare_iramuteq_corpus(
                    structured_data,
                    output_path,
                    doc_name=base_name,
                    include_metadata=True,
                )

                print(f"🗂️ Arquivo preparado: {output_path}")
            except Exception as e:
                print(f"❌ Erro ao processar {filename}: {str(e)}")


# Exemplo de uso
if __name__ == "__main__":
    # Configurações
    input_pdf_folder = (
        Path(__file__).parent.parent.parent / "pdf_files"
    )  # Pasta com seus PDFs
    output_text_folder = (
        Path(__file__).parent.parent.parent / "iramuteq_corpus"
    )  # Pasta de saída
    preserve_accentuation = False  # Mudar para True para manter acentos

    # Processar todos os PDFs na pasta
    process_pdf_folder(input_pdf_folder, output_text_folder, preserve_accentuation)

    print("\n 🎉 Processamento concluído. Os arquivos estão prontos para o IRaMuTeQ.")
