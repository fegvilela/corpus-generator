import PyPDF2
import re
import os
from unidecode import unidecode
from collections import defaultdict


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

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()

            # Processar a página para identificar elementos
            page_data = {
                "page_number": page_num,
                "content": text,
                "titles": [],
                "paragraphs": [],
                "tables": False,  # Placeholder - análise mais avançada necessária
                "figures": False,  # Placeholder - análise mais avançada necessária
            }

            # Identificar títulos (heurística simples - linhas com poucas palavras em caixa alta)
            lines = text.split("\n")
            for line in lines:
                clean_line = line.strip()
                words = clean_line.split()

                # Heurística para título
                if 1 <= len(words) <= 5 and clean_line.isupper():
                    page_data["titles"].append(clean_line)
                    result["titles"].append({"text": clean_line, "page": page_num})

            # Identificar parágrafos
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            page_data["paragraphs"] = paragraphs

            result["pages"].append(page_data)

    return result


def clean_text(text, preserve_accentuation=False):
    """
    Limpa e padroniza o texto com opções avançadas
    """
    # Normaliza espaços e quebras de linha
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    # Remove caracteres especiais (opcional)
    if not preserve_accentuation:
        text = unidecode(text)

    # Remove hifens no final de linhas (para palavras quebradas)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)

    # Remove cabeçalhos/rodapés com números de página
    text = re.sub(r"^\d+\s+|\s+\d+$", "", text, flags=re.MULTILINE)

    return text.strip()


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
            print(f"Processando: {filename}")

            try:
                # Extrair dados estruturados
                structured_data = pdf_to_structured_text(pdf_path)

                # Nome do arquivo de saída
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(output_folder, f"{base_name}_iramuteq.txt")

                # Preparar corpus
                prepare_iramuteq_corpus(
                    structured_data,
                    output_path,
                    doc_name=base_name,
                    include_metadata=True,
                )

                print(f"Arquivo preparado: {output_path}")
            except Exception as e:
                print(f"Erro ao processar {filename}: {str(e)}")


# Exemplo de uso
if __name__ == "__main__":
    # Configurações
    input_pdf_folder = "pdf_files"  # Pasta com seus PDFs
    output_text_folder = "iramuteq_corpus"  # Pasta de saída
    preserve_accentuation = False  # Mudar para True para manter acentos

    # Processar todos os PDFs na pasta
    process_pdf_folder(input_pdf_folder, output_text_folder, preserve_accentuation)

    print("\nProcessamento concluído. Os arquivos estão prontos para o IRaMuTeQ.")
