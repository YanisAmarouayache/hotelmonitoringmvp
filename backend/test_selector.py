import asyncio
from playwright.async_api import async_playwright

async def test_selector():
    url = "https://www.booking.com/hotel/fr/brach-paris.html"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🌐 Ouverture de la page...")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        
        print("\n🔍 Test des sélecteurs...")
        
        # Test 1: Compter tous les searchbox-dates-container
        containers = await page.query_selector_all('[data-testid="searchbox-dates-container"]')
        print(f"📊 Nombre total de searchbox-dates-container trouvés: {len(containers)}")
        
        # Test 2: Vérifier le sélecteur spécifique
        try:
            specific_element = await page.query_selector('#hp_availability_style_changes [data-testid="searchbox-dates-container"]')
            if specific_element:
                print("✅ Sélecteur spécifique fonctionne!")
                
                # Afficher les informations sur l'élément
                element_info = await page.evaluate("""
                    (element) => {
                        return {
                            tagName: element.tagName,
                            className: element.className,
                            textContent: element.textContent?.substring(0, 100),
                            isVisible: element.offsetParent !== null
                        };
                    }
                """, specific_element)
                print(f"   Élément: {element_info}")
                
            else:
                print("❌ Sélecteur spécifique ne trouve rien")
        except Exception as e:
            print(f"❌ Erreur avec le sélecteur spécifique: {e}")
        
        # Test 3: Lister tous les éléments avec leurs informations
        print("\n📋 Détails de tous les searchbox-dates-container:")
        for i, container in enumerate(containers):
            try:
                info = await page.evaluate("""
                    (element) => {
                        return {
                            tagName: element.tagName,
                            className: element.className,
                            textContent: element.textContent?.substring(0, 100),
                            isVisible: element.offsetParent !== null,
                            parentId: element.closest('[id]')?.id || 'no-id'
                        };
                    }
                """, container)
                print(f"  {i+1}. {info}")
            except Exception as e:
                print(f"  {i+1}. Erreur: {e}")
        
        print("\n🎯 Test de clic sur le deuxième élément...")
        if len(containers) >= 2:
            try:
                await containers[1].click()
                print("✅ Clic réussi sur le deuxième élément!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"❌ Erreur lors du clic: {e}")
        else:
            print("❌ Pas assez d'éléments pour tester le clic")
        
        print("\n⏸️ Appuyez sur Entrée pour fermer le navigateur...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_selector()) 