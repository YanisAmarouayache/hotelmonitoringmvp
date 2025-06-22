import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def record_clicks():
    """Ouvrir le navigateur et enregistrer tous les clics et requêtes GraphQL."""
    
    url = "https://www.booking.com/hotel/fr/brach-paris.html"
    graphql_responses = []
    clicks = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Enregistrer tous les clics
        async def on_click():
            # Récupérer la position de la souris et l'élément cliqué
            try:
                # Attendre un peu pour que le clic soit traité
                await page.wait_for_timeout(100)
                
                # Récupérer les informations sur l'élément cliqué
                element_info = await page.evaluate("""
                    () => {
                        const activeElement = document.activeElement;
                        if (activeElement) {
                            return {
                                tagName: activeElement.tagName,
                                id: activeElement.id,
                                className: activeElement.className,
                                dataTestId: activeElement.getAttribute('data-testid'),
                                ariaLabel: activeElement.getAttribute('aria-label'),
                                textContent: activeElement.textContent?.substring(0, 100),
                                timestamp: new Date().toISOString()
                            };
                        }
                        return null;
                    }
                """)
                
                if element_info:
                    clicks.append(element_info)
                    print(f"🖱️ Clic enregistré: {element_info}")
                    
            except Exception as e:
                print(f"Erreur lors de l'enregistrement du clic: {e}")
        
        # Intercepter les requêtes GraphQL
        async def on_response(response):
            if "/dml/graphql" in response.url:
                try:
                    body = await response.text()
                    try:
                        data = json.loads(body)
                        graphql_responses.append({
                            'url': response.url,
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        print(f"📡 GraphQL: {response.url}")
                        if 'availabilityCalendar' in str(data):
                            print("🎯 AVAILABILITY CALENDAR TROUVÉ!")
                            print(f"   URL: {response.url}")
                            print(f"   Données: {str(data)[:200]}...")
                            
                    except Exception:
                        pass
                except Exception as e:
                    print(f"Erreur lecture GraphQL: {e}")
        
        # Écouter les clics
        page.on("click", on_click)
        page.on("response", on_response)
        
        print("🌐 Ouverture de la page...")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        
        print("\n" + "="*60)
        print("🎯 NAVIGATEUR OUVERT - CLIQUEZ SUR LES ÉLÉMENTS !")
        print("="*60)
        print("Instructions:")
        print("1. Cliquez sur le bouton de date pour déclencher AvailabilityCalendar")
        print("2. Regardez la console pour voir les requêtes capturées")
        print("3. Appuyez sur Ctrl+C pour arrêter l'enregistrement")
        print("="*60)
        
        try:
            # Attendre que l'utilisateur arrête le script
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Arrêt de l'enregistrement...")
        
        await browser.close()
    
    # Sauvegarder les résultats
    results = {
        'url': url,
        'clicks': clicks,
        'graphql_responses': graphql_responses,
        'total_clicks': len(clicks),
        'total_graphql': len(graphql_responses),
        'recorded_at': datetime.now().isoformat()
    }
    
    with open('click_recording.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Résultats sauvegardés dans 'click_recording.json'")
    print(f"   Clics enregistrés: {len(clicks)}")
    print(f"   Requêtes GraphQL: {len(graphql_responses)}")
    
    # Afficher les clics
    if clicks:
        print("\n🖱️ Clics enregistrés:")
        for i, click in enumerate(clicks):
            print(f"  {i+1}. {click.get('tagName', '?')} - {click.get('dataTestId', 'no-testid')} - {click.get('textContent', 'no-text')[:50]}")

if __name__ == "__main__":
    asyncio.run(record_clicks()) 