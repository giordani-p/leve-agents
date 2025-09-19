#!/usr/bin/env python3
"""
Gerador de trilhas de aprendizado para testar o sistema de recomendação.
Cria trilhas com diferentes contextos, dificuldades e áreas para stress testing.
"""

import json
import uuid
import random
from typing import List, Dict, Any
from datetime import datetime
from faker import Faker

class TrailGenerator:
    def __init__(self, locale: str = "pt_BR"):
        self.fake = Faker(locale)
        self.difficulties = ["Beginner", "Intermediate", "Advanced"]
        self.statuses = ["Published", "Draft", "Archived"]
        self.lesson_kinds = ["reading", "practice", "video", "quiz"]
        self.lesson_statuses = ["Available", "Planned", "Locked"]
        self.content_statuses = ["Ready", "Draft", "Review"]
        
        # Áreas e contextos para diversificar as trilhas
        self.areas = [
            "Tecnologia", "Negócios", "Criatividade", "Saúde", "Educação",
            "Finanças", "Comunicação", "Liderança", "Vendas", "Marketing",
            "Design", "Engenharia", "Ciência", "Arte", "Esporte"
        ]
        
        self.tech_areas = [
            "Frontend", "Backend", "Mobile", "Data Science", "DevOps",
            "Cloud", "Cybersecurity", "AI/ML", "Blockchain", "IoT",
            "React", "Python", "JavaScript", "Java", "C#", "Go", "Rust"
        ]
        
        self.business_areas = [
            "Empreendedorismo", "Gestão", "Vendas", "Marketing Digital",
            "Análise de Dados", "Estratégia", "Operações", "RH",
            "Agile", "Scrum", "Lean", "Six Sigma", "PMI"
        ]
        
        # Templates mais realistas usando Faker
        self.trail_templates = {
            "Tecnologia": {
                "Beginner": [
                    "Introdução ao {tech_area}",
                    "Fundamentos de {tech_area}",
                    "{tech_area} do Zero",
                    "Primeiros Passos em {tech_area}",
                    "Aprenda {tech_area} Básico"
                ],
                "Intermediate": [
                    "Aprofundando {tech_area}",
                    "{tech_area} Intermediário",
                    "Dominando {tech_area}",
                    "Técnicas Avançadas em {tech_area}",
                    "{tech_area} Profissional"
                ],
                "Advanced": [
                    "Expert em {tech_area}",
                    "{tech_area} Masterclass",
                    "Arquitetura em {tech_area}",
                    "Padrões Avançados em {tech_area}",
                    "Especialização em {tech_area}"
                ]
            },
            "Negócios": {
                "Beginner": [
                    "Introdução ao {business_area}",
                    "Fundamentos de {business_area}",
                    "{business_area} para Iniciantes",
                    "Primeiros Passos em {business_area}",
                    "Básico de {business_area}"
                ],
                "Intermediate": [
                    "Aprofundando {business_area}",
                    "{business_area} Intermediário",
                    "Estratégias em {business_area}",
                    "Gestão Avançada em {business_area}",
                    "{business_area} Profissional"
                ],
                "Advanced": [
                    "Expert em {business_area}",
                    "Liderança em {business_area}",
                    "Estratégia Avançada em {business_area}",
                    "Masterclass de {business_area}",
                    "Especialização em {business_area}"
                ]
            }
        }

    def generate_trail(self, 
                      area: str, 
                      difficulty: str, 
                      context: str,
                      target_audience: str) -> Dict[str, Any]:
        """Gera uma trilha completa com módulos e lições."""
        
        # Gera ID único
        trail_id = str(uuid.uuid4())
        
        # Define título e descrição baseado no contexto
        title, subtitle, description = self._generate_trail_content(area, difficulty, context, target_audience)
        
        # Gera tags baseadas na área e contexto
        tags = self._generate_tags(area, difficulty, context)
        
        # Gera módulos (2-4 módulos por trilha)
        num_modules = self._get_num_modules(difficulty)
        modules = []
        
        for i in range(num_modules):
            module = self._generate_module(i + 1, area, difficulty, context)
            modules.append(module)
        
        return {
            "publicId": trail_id,
            "slug": self._generate_slug(title),
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "difficulty": difficulty,
            "tags": tags,
            "status": self._get_status(difficulty),
            "Modules": modules
        }

    def _generate_trail_content(self, area: str, difficulty: str, context: str, target_audience: str) -> tuple:
        """Gera título, subtítulo e descrição da trilha usando Faker."""
        
        # Seleciona área específica
        if area == "Tecnologia":
            specific_area = random.choice(self.tech_areas)
        elif area == "Negócios":
            specific_area = random.choice(self.business_areas)
        else:
            specific_area = area
        
        # Gera título usando templates
        if area in self.trail_templates:
            title_template = random.choice(self.trail_templates[area][difficulty])
            title = title_template.format(
                tech_area=specific_area, 
                business_area=specific_area
            )
        else:
            title = f"{specific_area} - {difficulty}"
        
        # Gera subtítulo usando Faker
        subtitle_templates = [
            f"Aprenda {specific_area} de forma prática",
            f"Domine {specific_area} com projetos reais",
            f"Desenvolva habilidades em {specific_area}",
            f"Torne-se especialista em {specific_area}",
            f"Evolua sua carreira com {specific_area}"
        ]
        subtitle = random.choice(subtitle_templates)
        
        # Gera descrição usando Faker com sentenças mais realistas
        description_parts = [
            f"Esta trilha de {specific_area} foi desenvolvida para {target_audience}.",
            f"Aprenda os conceitos fundamentais e avance para técnicas avançadas.",
            f"Inclui projetos práticos, exercícios hands-on e casos reais da indústria.",
            f"Desenvolvida por especialistas com anos de experiência no mercado.",
            f"Perfeita para quem quer {self.fake.sentence(nb_words=6).lower().rstrip('.')}."
        ]
        
        # Seleciona 2-3 partes para a descrição
        selected_parts = random.sample(description_parts, random.randint(2, 3))
        description = " ".join(selected_parts)
        
        return title, subtitle, description

    def _generate_tags(self, area: str, difficulty: str, context: str) -> List[str]:
        """Gera tags relevantes para a trilha."""
        tags = [area, difficulty]
        
        if area == "Tecnologia":
            tags.extend(random.sample(self.tech_areas, 2))
        elif area == "Negócios":
            tags.extend(random.sample(self.business_areas, 2))
        
        # Adiciona tags baseadas no contexto
        context_tags = {
            "carreira": ["Carreira", "Profissional", "Mercado"],
            "academico": ["Acadêmico", "Estudos", "Universidade"],
            "pessoal": ["Pessoal", "Desenvolvimento", "Crescimento"],
            "empreendedorismo": ["Empreendedorismo", "Startup", "Inovação"]
        }
        
        if context in context_tags:
            tags.extend(context_tags[context])
        
        return list(set(tags))  # Remove duplicatas

    def _generate_slug(self, title: str) -> str:
        """Gera slug a partir do título."""
        import re
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def _get_num_modules(self, difficulty: str) -> int:
        """Define número de módulos baseado na dificuldade."""
        module_counts = {
            "Beginner": [2, 3],
            "Intermediate": [3, 4],
            "Advanced": [4, 5]
        }
        import random
        return random.choice(module_counts[difficulty])

    def _get_status(self, difficulty: str) -> str:
        """Define status baseado na dificuldade com mais variação."""
        status_weights = {
            "Beginner": {"Published": 0.7, "Draft": 0.2, "Archived": 0.1},
            "Intermediate": {"Published": 0.6, "Draft": 0.25, "Archived": 0.15},
            "Advanced": {"Published": 0.5, "Draft": 0.3, "Archived": 0.2}
        }
        import random
        return random.choices(
            list(status_weights[difficulty].keys()),
            weights=list(status_weights[difficulty].values())
        )[0]

    def _generate_module(self, order: int, area: str, difficulty: str, context: str) -> Dict[str, Any]:
        """Gera um módulo completo com lições."""
        module_id = str(uuid.uuid4())
        
        # Títulos de módulos baseados na área e ordem
        module_titles = {
            "Tecnologia": [
                "Fundamentos e Conceitos Básicos",
                "Implementação Prática",
                "Projetos e Aplicações",
                "Otimização e Performance",
                "Arquitetura Avançada"
            ],
            "Negócios": [
                "Conceitos Fundamentais",
                "Estratégias Práticas",
                "Implementação e Execução",
                "Análise e Métricas",
                "Liderança e Gestão"
            ]
        }
        
        if area in module_titles and order <= len(module_titles[area]):
            title = f"Módulo {order} — {module_titles[area][order-1]}"
        else:
            title = f"Módulo {order} — Conceitos e Práticas"
        
        # Gera lições (2-4 lições por módulo)
        num_lessons = self._get_num_lessons(difficulty)
        lessons = []
        
        for i in range(num_lessons):
            lesson = self._generate_lesson(i + 1, area, difficulty, context)
            lessons.append(lesson)
        
        return {
            "publicId": module_id,
            "title": title,
            "order": order,
            "contentStatus": self._get_content_status(difficulty),
            "Lessons": lessons
        }

    def _get_num_lessons(self, difficulty: str) -> int:
        """Define número de lições baseado na dificuldade."""
        lesson_counts = {
            "Beginner": [2, 3],
            "Intermediate": [3, 4],
            "Advanced": [4, 5]
        }
        import random
        return random.choice(lesson_counts[difficulty])

    def _get_content_status(self, difficulty: str) -> str:
        """Define status do conteúdo baseado na dificuldade."""
        status_weights = {
            "Beginner": {"Ready": 0.8, "Draft": 0.2},
            "Intermediate": {"Ready": 0.7, "Draft": 0.3},
            "Advanced": {"Ready": 0.6, "Draft": 0.4}
        }
        import random
        return random.choices(
            list(status_weights[difficulty].keys()),
            weights=list(status_weights[difficulty].values())
        )[0]

    def _generate_lesson(self, order: int, area: str, difficulty: str, context: str) -> Dict[str, Any]:
        """Gera uma lição completa."""
        lesson_id = str(uuid.uuid4())
        
        # Seleciona tipo de lição
        import random
        lesson_kind = random.choice(self.lesson_kinds)
        
        # Títulos de lições baseados no tipo e área
        lesson_titles = {
            "reading": [
                "Conceitos Fundamentais",
                "Teoria e Prática",
                "Fundamentos Teóricos",
                "Base Conceitual"
            ],
            "practice": [
                "Exercícios Práticos",
                "Implementação Hands-on",
                "Projetos Práticos",
                "Aplicação Real"
            ],
            "video": [
                "Demonstração Prática",
                "Tutorial em Vídeo",
                "Exemplos Visuais",
                "Demonstração Interativa"
            ],
            "quiz": [
                "Teste de Conhecimento",
                "Avaliação Prática",
                "Quiz Interativo",
                "Verificação de Aprendizado"
            ]
        }
        
        title = f"Lição {order} — {random.choice(lesson_titles[lesson_kind])}"
        
        # Gera dados específicos do tipo de lição
        data = self._generate_lesson_data(lesson_kind, area, difficulty)
        
        return {
            "publicId": lesson_id,
            "title": title,
            "order": order,
            "lessonKind": lesson_kind,
            "lessonStatus": random.choice(self.lesson_statuses),
            "lockReason": None,
            "contentStatus": self._get_content_status(difficulty),
            "data": data
        }

    def _generate_lesson_data(self, lesson_kind: str, area: str, difficulty: str) -> Dict[str, Any]:
        """Gera dados específicos para cada tipo de lição."""
        import random
        
        if lesson_kind == "reading":
            return {
                "conteudo": f"Conteúdo teórico sobre {area} com exemplos práticos e exercícios guiados."
            }
        elif lesson_kind == "practice":
            exercises = [
                "Implementar conceito básico",
                "Criar projeto prático",
                "Resolver problema real",
                "Aplicar técnica aprendida"
            ]
            return {
                "exercicios": random.sample(exercises, random.randint(2, 4))
            }
        elif lesson_kind == "video":
            return {
                "videoUrl": f"https://example.com/video-{random.randint(1000, 9999)}",
                "dicas": ["Assista com atenção", "Pause para praticar", "Anote os pontos importantes"]
            }
        elif lesson_kind == "quiz":
            questions = [
                {"q": "Qual é o conceito principal?", "a": ["Opção A", "Opção B", "Opção C"]},
                {"q": "Como aplicar na prática?", "a": ["Método 1", "Método 2", "Método 3"]},
                {"q": "Qual é a melhor abordagem?", "a": ["Abordagem 1", "Abordagem 2", "Abordagem 3"]},
                {"q": "O que você aprendeu?", "a": ["Conceito 1", "Conceito 2", "Conceito 3"]}
            ]
            num_questions = random.randint(1, min(3, len(questions)))
            return {
                "perguntas": random.sample(questions, num_questions)
            }
        
        return {}

    def generate_trail_batch(self, num_trails: int = 50) -> List[Dict[str, Any]]:
        """Gera um lote de trilhas com diversidade."""
        trails = []
        
        # Contextos e audiências para diversificar
        contexts = ["carreira", "academico", "pessoal", "empreendedorismo"]
        target_audiences = ["iniciantes", "intermediarios", "avancados", "profissionais"]
        
        for i in range(num_trails):
            import random
            
            area = random.choice(self.areas)
            difficulty = random.choice(self.difficulties)
            context = random.choice(contexts)
            audience = random.choice(target_audiences)
            
            trail = self.generate_trail(area, difficulty, context, audience)
            trails.append(trail)
        
        return trails

    def save_trails(self, trails: List[Dict[str, Any]], filename: str = "generated_trails.json"):
        """Salva as trilhas geradas em arquivo JSON."""
        filepath = f"/Users/pablo.giordani/Documents/repo-pg/my-agents/leve-agents/files/trails/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(trails, f, ensure_ascii=False, indent=2)
        
        print(f"{len(trails)} trilhas salvas em {filepath}")

if __name__ == "__main__":
    generator = TrailGenerator()
    
    # Gera 100 trilhas diversificadas
    print("Gerando trilhas diversificadas...")
    trails = generator.generate_trail_batch(100)
    
    # Salva as trilhas
    generator.save_trails(trails, "generated_trails_extended.json")
    
    print(f"Estatísticas das trilhas geradas:")
    print(f"   - Total: {len(trails)}")
    
    # Conta por dificuldade
    difficulties = {}
    for trail in trails:
        diff = trail['difficulty']
        difficulties[diff] = difficulties.get(diff, 0) + 1
    
    for diff, count in difficulties.items():
        print(f"   - {diff}: {count}")
    
    print("✨ Geração concluída!")
