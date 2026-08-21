from pathlib import Path
import csv
import hashlib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

ARQUIVO = BASE_DIR / "data" / "vendas_masterdetprd.csv"


# funções auxiliares
def anonimizar_cliente(cpf_cnpj):
    if not cpf_cnpj:
        return None

    cpf_cnpj = cpf_cnpj.strip()

    # consumidor não identificado
    if not cpf_cnpj or cpf_cnpj == "00000000000000":
        return None

    hash_cliente = hashlib.sha256(
        cpf_cnpj.encode("utf-8")
    ).hexdigest()[:10]

    return f"C{hash_cliente}"


def converter_numero(valor):
    if not valor:
        return None

    valor = valor.strip()

    try:
        return float(
            valor.replace(".", "").replace(",", ".")
        )

    except ValueError:
        return None


# variáveis
vendas = []

venda_atual = None
data_atual = None
hora_atual = None
cliente_atual = None

dentro_dos_itens = False #indica se já chegamos no cabeçalho "Item" da venda atual.


# Leitura do CSV
with open(ARQUIVO, "r", encoding="latin1", newline="") as arquivo:
    leitor = csv.reader(arquivo, delimiter=";")
    for linha in leitor:
        if not linha:
            continue
        tipo = linha[0].strip()

        # é "Nro Venda"?
        if tipo == "Nro Venda":

            venda_atual = None
            data_atual = None
            hora_atual = None
            cliente_atual = None

            dentro_dos_itens = False

            continue
        # é a linha de dados da venda?
        if (venda_atual is None and len(linha) > 20 and linha[0].strip().isdigit()):
            venda_atual = linha[0].strip()
            data_atual = linha[1].strip()
            hora_atual = linha[3].strip()
            cpf_cnpj = linha[7].strip()
            nome_cliente = linha[20].strip()
            # Consumidor Final
            if (nome_cliente.upper() == "CONSUMIDOR FINAL"):
                cliente_atual = None # consumidor não identificado
            else:
                cliente_atual = anonimizar_cliente(cpf_cnpj)
            continue

        # é a linha de cabeçalho "Item"?
        if tipo == "Item":
            dentro_dos_itens = True
            continue
        # é a linha de dados do item da venda?
        if (dentro_dos_itens and tipo.isdigit() and venda_atual is not None):

            # tem pelo menos 14 colunas?
            if len(linha) < 14:
                continue
            codigo_produto = linha[0].strip()
            descricao = linha[1].strip()

            # converte quantidade, preço e total para float
            quantidade = converter_numero(linha[8])

            preco = converter_numero(linha[10])

            total = converter_numero(linha[12])

            if not descricao:
                continue

            # adiciona produto à lista de vendas
            vendas.append({

                "venda_id": venda_atual,

                "data": data_atual,

                "hora": hora_atual,

                "cliente_id": cliente_atual,

                "produto_id": codigo_produto,

                "produto": descricao,

                "quantidade": quantidade,

                "preco_unitario": preco,

                "valor_total": total,
            })


df = pd.DataFrame(vendas)



# resultado
print()
if df.empty:

    print("\nNenhum produto foi encontrado.")

else:

    print(
        f"\nTotal de itens: "
        f"{len(df)}"
    )

    print(
        f"Total de vendas: "
        f"{df['venda_id'].nunique()}"
    )

    print(
        f"Clientes identificados: "
        f"{df['cliente_id'].nunique()}"
    )

    print(
        f"Itens sem cliente identificado: "
        f"{df['cliente_id'].isna().sum()}"
    )
   
    print(
        f"Produtos diferentes: "
        f"{df['produto_id'].nunique()}"
    )

    print("COMPRAS POR CLIENTE")

    compras_por_cliente = (
        df.dropna(subset=["cliente_id"])
        .groupby("cliente_id")["venda_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    print(compras_por_cliente.describe())

    print("\n10 clientes com mais compras:")
    print(compras_por_cliente.head(10))

    print("\nClientes com apenas 1 compra:")
    print((compras_por_cliente == 1).sum())

# salvar CSV
caminho_saida = BASE_DIR / "data" / "vendas_anonimizadas.csv"
df.to_csv(caminho_saida, index=False, sep=";", encoding="utf-8")