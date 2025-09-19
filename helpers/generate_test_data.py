#!/usr/bin/env python3
"""
Script simples para gerar dados de teste.
Usa os geradores específicos para criar trilhas e usuários.
"""

from trail_generator import TrailGenerator
from user_generator import UserGenerator

def main():
    print(" Gerando dados de teste...")
    
    # Gerar trilhas
    print("\n Gerando trilhas...")
    trail_gen = TrailGenerator()
    trails = trail_gen.generate_trail_batch(200)
    trail_gen.save_trails(trails, "trails_faker.json")
    
    # Gerar usuários  
    print("\n Gerando usuários...")
    user_gen = UserGenerator()
    users = user_gen.generate_user_batch(300)
    user_gen.save_users(users, "users_faker.json")
    
    print("\nGeração concluída!")
    print(f"   - {len(trails)} trilhas salvas")
    print(f"   - {len(users)} usuários salvos")

if __name__ == "__main__":
    main()