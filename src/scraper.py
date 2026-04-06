
from playwright.async_api import async_playwright
import asyncio
import pandas as pd

async def scrape_reclamacoes():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"        )
        page = await context.new_page()

        # pra navegar pela página pra gerar o cf_clearance válido
        await page.goto("https://www.reclameaqui.com.br/empresa/claro/lista-reclamacoes/")
        await asyncio.sleep(3)  # pra aguardar o Cloudflare resolver

        reclamacoes = []
        for offset in range(0, 5000, 5):
            url = f"https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/query/companyComplains/5/{offset}?company=7712"

            try:
                response = await page.evaluate(f"""
                    fetch('{url}', {{
                        headers: {{
                            'Accept': 'application/json',
                            'Origin': 'https://www.reclameaqui.com.br',
                            'Referer': 'https://www.reclameaqui.com.br/'
                        }}
                    }}).then(r => r.json())
                """)

                complains = response['complainResult']['complains']['data']

                if not complains:
                    print(f"offset {offset} — sem mais dados, encerrando")
                    break

                reclamacoes.extend(complains)
                print(f"offset {offset} — {len(complains)} reclamações coletadas | total: {len(reclamacoes)}")

            except Exception as e:
                print(f"offset {offset} — limite da API atingido, encerrando coleta")
                break

            await asyncio.sleep(1.5)

        await browser.close()
        return reclamacoes

reclamacoes = asyncio.run(scrape_reclamacoes())
df_reclamacoes = pd.DataFrame(reclamacoes)
# pra salvar o CSV direto na pasta correta do repositório
df_reclamacoes.to_csv("data/reclamacoes_claro.csv", index=False)
# e depois mostrar um resumo do que foi coletado
print(f"\nTotal coletado: {df_reclamacoes.shape}")
print(df_reclamacoes.columns.tolist())
