import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    url = "https://www.booking.com/hotel/fr/brach-paris.html"

    graphql_responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Intercepter les requêtes vers /dml/graphql
        async def on_response(response):
            if "/dml/graphql" in response.url:
                try:
                    body = await response.text()
                    print(f"\n--- GraphQL Response from {response.url} ---\n{body[:500]}...\n")
                    # Essayer de parser le JSON
                    try:
                        data = json.loads(body)
                        graphql_responses.append(data)
                    except Exception:
                        graphql_responses.append({"url": response.url, "raw": body})
                except Exception as e:
                    print(f"Erreur lors de la lecture de la réponse GraphQL: {e}")

        page.on("response", on_response)

        print(f"Ouverture de la page: {url}")
        await page.goto(url)
        await page.wait_for_timeout(3000)

        print("Attente de 5 secondes pour que tu puisses cliquer manuellement sur le deuxième bouton de date...")
        print("Ou le script va cliquer automatiquement sur le deuxième bouton dans 5 secondes...")
        await page.wait_for_timeout(5000)

        print("Clic automatique sur le DEUXIÈME bouton de date (date-display-field-end)...")
        try:
            await page.click('[data-testid="date-display-field-end"]')
            print("Clic réussi sur le deuxième bouton de date")
        except Exception as e:
            print(f"Erreur lors du clic automatique: {e}")
            print("Tu peux cliquer manuellement sur le deuxième bouton de date maintenant...")

        print("Attente de 10 secondes pour capturer les requêtes GraphQL...")
        await page.wait_for_timeout(10000)

        await browser.close()

    # Sauvegarder toutes les réponses dans un fichier
    with open("playwright_graphql_results.json", "w", encoding="utf-8") as f:
        json.dump(graphql_responses, f, indent=2, ensure_ascii=False)
    print("\nToutes les réponses GraphQL sauvegardées dans playwright_graphql_results.json")

if __name__ == "__main__":
    asyncio.run(run()) 