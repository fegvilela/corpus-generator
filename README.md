# **📂 Estrutura do Projeto iramuteq_preprocessor**

_Automatização de pré-processamento de textos para o IRaMuTeQ_

Este projeto organiza e processa arquivos PDF para gerar corpus textuais compatíveis com o [IRaMuTeQ](http://www.iramuteq.org/). O **Makefile** simplifica a configuração do ambiente e execução do pipeline.

---

## **📂 Estrutura de Diretórios**

```
iramuteq_preprocessor/
├── .venv/                  # Ambiente virtual Python (gerado automaticamente)
├── pdf_files/              # ⚠️ Pasta para usuário colocar arquivos PDF de entrada
├── iramuteq_corpus/        # ✅ Pasta gerada com os textos processados (outputs)
├── src/                    # Código-fonte do pré-processador
│   └── iramuteq_preprocessor/
│       ├── main.py         # Script principal
│       └── (outros módulos)
├── pyproject.toml          # Dependências gerenciadas pelo Poetry
├── Makefile                # Automação de tarefas
└── README.md               # Este guia
```

---

## **⚙️ Configuração Inicial**

### **1. Clone o repositório**

```bash
git clone [URL_DO_REPOSITÓRIO]
cd iramuteq_preprocessor
```

### **2. Crie as pastas de dados** _(opcional)_

```bash
mkdir -p pdf_files iramuteq_corpus  # Cria pastas se não existirem
```

### **3. Instalação automática**

```bash
make setup
```

**O que isso faz?**  
✔ Instala Python e Poetry (se necessário)  
✔ Cria ambiente virtual (`.venv`)  
✔ Instala dependências do projeto

---

## **🚀 Como Usar**

### **Passo 1: Adicione arquivos PDF**

Coloque os arquivos a serem processados em:

```
pdf_files/
  ├── documento1.pdf
  ├── documento2.pdf
  └── ...
```

### **Passo 2: Execute o pré-processamento**

```bash
make run
```

**Saídas geradas em:**

```
iramuteq_corpus/
  ├── documento1_iramuteq.txt
  ├── documento2_iramuteq.txt
  └── ...
```

### **Passo 3: Use os arquivos no IRaMuTeQ**

Copie os textos processados (`iramuteq_corpus/*.txt`) para análise no software.

---

## **📋 Comandos Úteis**

| Comando             | Descrição                                                    |
| ------------------- | ------------------------------------------------------------ |
| **`make setup`**    | Configura o ambiente completo                                |
| **`make run`**      | Processa todos os PDFs da pasta de entrada                   |
| **`make clean`**    | Remove arquivos temporários (_ajustar conforme necessidade_) |
| **`make activate`** | Ativa o ambiente virtual (`eval "$(make activate)"`)         |

---

## **❓ Solução de Problemas**

### **Erro: "Pasta pdf_files não encontrada"**

Crie a pasta manualmente:

```bash
mkdir pdf_files
```

### **Erro: Dependências faltando**

Reinstale as dependências:

```bash
make install-deps
```

### **Ambiente virtual não ativado**

Ative-o com:

```bash
eval "$(make activate)"
```

---

## **🔧 Personalização**

### **Se precisar modificar:**

1. **Locais das pastas**: Ajuste os caminhos em `src/iramuteq_preprocessor/main.py`.
2. **Regras de processamento**: Edite os módulos em `src/`.

---

## **📌 Boas Práticas**

✅ **Organize os PDFs** em subpastas dentro de `pdf_files/` se necessário.  
✅ **Verifique os outputs** em `iramuteq_corpus/` antes de usar no IRaMuTeQ.  
✅ **Sempre use `make run`** para garantir o processamento correto.

---

> **Pronto!** Agora você pode converter PDFs em corpus textuais de forma automatizada.  
> Para dúvidas, consulte a documentação do [IRaMuTeQ](http://www.iramuteq.org/documentation).
