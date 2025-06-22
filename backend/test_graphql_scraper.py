#!/usr/bin/env python3
"""
Test script for the Booking.com GraphQL scraper
"""

import sys
import os
import json
from datetime import datetime

# Add the scraper directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from booking_graphql_scraper import BookingGraphQLScraper

def test_brach_hotel():
    """Test the GraphQL scraper with the Brach hotel URL."""
    
    # URL de l'hôtel Brach fournie
    brach_url = "https://www.booking.com/hotel/fr/brach-paris.html?ssne=Paris&ssne_untouched=Paris&highlighted_hotels=3593025&ss=Paris&dest_id=-1456928&dest_type=city&hp_avform=1&origin=hp&do_availability_check=1&label=brach-paris-zZ9WH8N2TuY83vvNrEJaAwS410071049405%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-447709349445%3Alp1006094%3Ali%3Adec%3Adm%3Appccp%3DUmFuZG9tSVYkc2RlIyh9YTQUGSsRwx9_3qo3uPTHyoo&sid=7ef522001e29f4651cee7b8c1851cc55&aid=311984&lang=en-gb&sb=1&src_elem=sb&src=hotel&checkin=2025-06-23&checkout=2025-06-24&group_adults=2&no_rooms=1&group_children=1&age=1#group_recommendation"
    
    print("=== Test du scraper GraphQL Booking.com ===")
    print(f"URL de test: {brach_url}")
    print()
    
    # Créer l'instance du scraper
    scraper = BookingGraphQLScraper()
    
    # Test 1: Extraction de l'ID de l'hôtel
    print("1. Extraction de l'ID de l'hôtel...")
    hotel_id = scraper.extract_hotel_id_from_url(brach_url)
    print(f"   Hotel ID extrait de l'URL: {hotel_id}")
    
    if not hotel_id:
        print("   Tentative d'extraction depuis la page...")
        hotel_id = scraper.get_hotel_id_from_page(brach_url)
        print(f"   Hotel ID extrait de la page: {hotel_id}")
    
    print()
    
    # Test 2: Extraction des paramètres de l'URL
    print("2. Extraction des paramètres de l'URL...")
    url_params = scraper.extract_url_parameters(brach_url)
    print(f"   Paramètres extraits: {len(url_params)} paramètres")
    for key, value in list(url_params.items())[:10]:  # Afficher les 10 premiers
        print(f"   {key}: {value}")
    if len(url_params) > 10:
        print(f"   ... et {len(url_params) - 10} autres paramètres")
    print()
    
    # Test 3: Récupération du calendrier de disponibilité
    print("3. Récupération du calendrier de disponibilité...")
    calendar_result = scraper.get_availability_calendar(brach_url, hotel_id)
    
    if 'error' in calendar_result:
        print(f"   ❌ Erreur: {calendar_result['error']}")
    else:
        print(f"   ✅ Succès!")
        print(f"   Hotel ID: {calendar_result.get('hotel_id')}")
        print(f"   Jours disponibles: {calendar_result.get('total_available_days')}")
        
        # Afficher quelques exemples de prix
        days = calendar_result.get('days', [])
        if days:
            print(f"   Exemples de prix:")
            for i, day in enumerate(days[:5]):  # Afficher les 5 premiers
                print(f"     {day['checkin']}: {day['price_formatted']} (€{day['price']})")
            if len(days) > 5:
                print(f"     ... et {len(days) - 5} autres jours")
    
    print()
    
    # Test 4: Récupération des informations de base de l'hôtel
    print("4. Récupération des informations de base de l'hôtel...")
    hotel_info = scraper._get_hotel_basic_info(brach_url)
    
    if hotel_info:
        print(f"   ✅ Informations récupérées:")
        for key, value in hotel_info.items():
            print(f"     {key}: {value}")
    else:
        print("   ❌ Aucune information récupérée")
    
    print()
    
    # Test 5: Scraping complet
    print("5. Scraping complet (hôtel + prix)...")
    full_result = scraper.scrape_hotel_with_pricing(brach_url)
    
    if 'error' in full_result:
        print(f"   ❌ Erreur: {full_result['error']}")
    else:
        print(f"   ✅ Scraping complet réussi!")
        print(f"   Données hôtel: {len(full_result.get('hotel_data', {}))} champs")
        print(f"   Données prix: {full_result.get('pricing_data', {}).get('total_available_days', 0)} jours")
    
    print()
    print("=== Fin du test ===")
    
    # Sauvegarder les résultats dans un fichier JSON
    results = {
        'test_timestamp': datetime.now().isoformat(),
        'test_url': brach_url,
        'hotel_id_extraction': hotel_id,
        'url_parameters': url_params,
        'calendar_result': calendar_result,
        'hotel_basic_info': hotel_info,
        'full_scraping_result': full_result
    }
    
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("Résultats sauvegardés dans 'test_results.json'")

if __name__ == "__main__":
    test_brach_hotel() 