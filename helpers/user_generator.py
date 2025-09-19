#!/usr/bin/env python3
"""
Gerador de perfis de usuários para testar o sistema de recomendação.
Cria usuários com diferentes contextos, perfis DISC, e situações para stress testing.
"""

import json
import uuid
import random
from typing import List, Dict, Any
from faker import Faker

class UserGenerator:
    def __init__(self, locale: str = "pt_BR"):
        self.fake = Faker(locale)
        
        # Dados para gerar perfis diversos
        self.idades = ["18-24", "25-30", "31-35", "36-40", "41-45", "46-50", "51+"]
        
        self.estagios_escolares = [
            "concluinte do ensino médio", "estudante universitário", "formado no ensino superior",
            "pós-graduação", "mestrado", "doutorado", "técnico", "profissionalizante"
        ]
        
        self.cursos = [
            "Ciência da Computação", "Engenharia de Software", "Sistemas de Informação",
            "Administração", "Marketing", "Psicologia", "Medicina", "Direito", "Economia",
            "Jornalismo", "Design", "Arquitetura", "Engenharia Civil", "Pedagogia",
            "Contabilidade", "Relações Internacionais", "Publicidade", "Fisioterapia"
        ]
        
        self.objetivos_carreira = [
            "Conseguir o primeiro emprego", "Mudar de área profissional", "Avançar na carreira atual",
            "Empreender", "Trabalhar remotamente", "Trabalhar no exterior", "Trabalhar em startup",
            "Trabalhar em multinacional", "Ser freelancer", "Ser consultor", "Ser professor",
            "Trabalhar com tecnologia", "Trabalhar com dados", "Trabalhar com marketing",
            "Trabalhar com vendas", "Trabalhar com design", "Trabalhar com saúde"
        ]
        
        self.habilidades_tecnicas = [
            "Programação básica", "Excel avançado", "PowerPoint", "Word", "Google Workspace",
            "Redes sociais", "Marketing digital", "Design gráfico", "Fotografia", "Vídeo",
            "Inglês intermediário", "Espanhol básico", "Matemática", "Estatística",
            "Análise de dados", "Gestão de projetos", "Vendas", "Atendimento ao cliente",
            "Comunicação", "Liderança", "Trabalho em equipe", "Organização", "Criatividade"
        ]
        
        self.habilidades_comportamentais = [
            "Comunicação", "Liderança", "Trabalho em equipe", "Criatividade", "Proatividade",
            "Resiliência", "Adaptabilidade", "Empatia", "Organização", "Foco",
            "Determinação", "Curiosidade", "Pensamento crítico", "Resolução de problemas",
            "Gestão do tempo", "Inteligência emocional", "Negociação", "Persuasão"
        ]
        
        self.perfis_disc = [
            "Alto D - Médio I", "Alto I - Médio S", "Alto S - Médio C", "Alto C - Médio D",
            "Médio D - Alto I", "Médio I - Alto S", "Médio S - Alto C", "Médio C - Alto D",
            "Alto D - Alto I", "Alto I - Alto S", "Alto S - Alto C", "Alto C - Alto D"
        ]
        
        self.talentos_clifton = [
            "Realização", "Iniciativa", "Conector", "Empatia", "Analítico", "Estratégico",
            "Foco", "Executor", "Harmonia", "Responsabilidade", "Desenvolvedor", "Positivo",
            "Comando", "Competição", "Comunicação", "Contexto", "Deliberativo", "Disciplina",
            "Individualização", "Input", "Intellection", "Learner", "Maximizer", "Relator",
            "Self-Assurance", "Significance", "Woo", "Adaptability", "Arranger", "Belief",
            "Consistency", "Developer", "Fairness", "Ideation", "Includer", "Restorative"
        ]
        
        self.areas_interesse = [
            "Tecnologia", "Negócios", "Criatividade", "Saúde", "Educação", "Finanças",
            "Comunicação", "Liderança", "Vendas", "Marketing", "Design", "Engenharia",
            "Ciência", "Arte", "Esporte", "Gastronomia", "Moda", "Música", "Cinema"
        ]

    def generate_user(self, 
                     perfil_tipo: str = "aleatorio",
                     contexto_especifico: str = None) -> Dict[str, Any]:
        """Gera um perfil de usuário completo usando Faker."""
        
        # Gera dados básicos usando Faker
        nome = self.fake.first_name()
        idade = random.choice(self.idades)
        localizacao = f"{self.fake.city()} - {self.fake.state_abbr()}"
        
        # Gera dados pessoais
        dados_pessoais = self._generate_dados_pessoais(nome, idade, localizacao)
        
        # Gera situação acadêmica baseada no perfil
        situacao_academica = self._generate_situacao_academica(perfil_tipo)
        
        # Gera objetivos de carreira
        objetivos_carreira = self._generate_objetivos_carreira(perfil_tipo, contexto_especifico)
        
        # Gera habilidades e competências
        habilidades_competencias = self._generate_habilidades_competencias(perfil_tipo)
        
        # Gera preferências de aprendizado
        preferencias_aprendizado = self._generate_preferencias_aprendizado(perfil_tipo)
        
        # Gera aspirações profissionais
        aspiracoes_profissionais = self._generate_aspiracoes_profissionais(perfil_tipo)
        
        # Gera barreiras e desafios
        barreiras_desafios = self._generate_barreiras_desafios(perfil_tipo)
        
        # Gera interesses pessoais
        interesses_pessoais = self._generate_interesses_pessoais(perfil_tipo)
        
        # Gera contexto socioeconômico
        contexto_socioeconomico = self._generate_contexto_socioeconomico(perfil_tipo)
        
        # Gera perfil DISC
        perfil_disc = self._generate_perfil_disc(perfil_tipo)
        
        # Gera talentos CliftonStrengths
        talentos_cliftonstrengths = self._generate_talentos_cliftonstrengths(perfil_tipo)
        
        return {
            "dados_pessoais": dados_pessoais,
            "situacao_academica": situacao_academica,
            "objetivos_carreira": objetivos_carreira,
            "habilidades_competencias": habilidades_competencias,
            "preferencias_aprendizado": preferencias_aprendizado,
            "aspiracoes_profissionais": aspiracoes_profissionais,
            "barreiras_desafios": barreiras_desafios,
            "interesses_pessoais": interesses_pessoais,
            "contexto_socioeconomico": contexto_socioeconomico,
            "perfil_disc": perfil_disc,
            "talentos_cliftonstrengths": talentos_cliftonstrengths
        }

    def _generate_dados_pessoais(self, nome: str, idade: str, localizacao: str) -> Dict[str, Any]:
        """Gera dados pessoais básicos usando Faker."""
        return {
            "nome_preferido": nome,
            "idade": idade,
            "localizacao": localizacao,
            "disponibilidade_tempo": random.choice([
                "Fins de semana", "Noturno", "Manhã", "Tarde", "Flexível", "Meio-período"
            ])
        }

    def _generate_situacao_academica(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera situação acadêmica baseada no perfil."""
        estagio = random.choice(self.estagios_escolares)
        
        if perfil_tipo == "universitario":
            curso = random.choice(self.cursos)
            instituicao = random.choice([
                "Universidade Federal", "Universidade Estadual", "Universidade Privada",
                "Instituto Federal", "Faculdade Particular"
            ])
            ano_inicio = str(random.randint(2018, 2024))
            previsao_formatura = str(int(ano_inicio) + random.randint(3, 6))
            nota_media = f"{random.uniform(6.0, 10.0):.1f}"
        else:
            curso = "Não especificado" if estagio == "concluinte do ensino médio" else random.choice(self.cursos)
            instituicao = "Não especificada"
            ano_inicio = "Não especificado"
            previsao_formatura = "Não especificada"
            nota_media = "Não especificada"
        
        return {
            "estagio_escolar": estagio,
            "curso_atual": curso,
            "instituicao": instituicao,
            "ano_inicio": ano_inicio,
            "previsao_formatura": previsao_formatura,
            "nota_media": nota_media,
            "materias_favoritas": random.sample(self.areas_interesse, random.randint(2, 4)),
            "materias_dificuldade": random.sample(self.areas_interesse, random.randint(1, 3))
        }

    def _generate_objetivos_carreira(self, perfil_tipo: str, contexto_especifico: str) -> Dict[str, Any]:
        """Gera objetivos de carreira baseados no perfil usando Faker."""
        objetivo_principal = random.choice(self.objetivos_carreira)
        
        if contexto_especifico:
            if contexto_especifico == "tecnologia":
                objetivo_principal = random.choice([
                    "Conseguir primeiro emprego como desenvolvedor",
                    "Migrar para área de tecnologia",
                    "Especializar-se em IA/ML",
                    "Trabalhar como freelancer tech"
                ])
            elif contexto_especifico == "negocios":
                objetivo_principal = random.choice([
                    "Abrir meu próprio negócio",
                    "Trabalhar em consultoria",
                    "Liderar equipe de vendas",
                    "Especializar-se em marketing digital"
                ])
        
        # Usa Faker para gerar objetivos mais realistas
        area_interesse = random.choice(self.areas_interesse)
        objetivos_especificos = [
            f"Desenvolver habilidades em {area_interesse}",
            f"Aprender {self.fake.word().title()} para {self.fake.sentence(nb_words=3).lower().rstrip('.')}",
            "Criar portfólio profissional",
            "Expandir rede de contatos",
            f"Especializar-se em {self.fake.job()}"
        ]
        
        metas_temporais = {
            "curto_prazo": [
                f"Completar {self.fake.word().title()} em 3 meses",
                "Atualizar currículo",
                "Fazer networking profissional"
            ],
            "medio_prazo": [
                "Conseguir entrevistas",
                f"Desenvolver projeto em {area_interesse}",
                "Ganhar experiência prática"
            ],
            "longo_prazo": [
                f"Trabalhar como {self.fake.job()}",
                "Crescer profissionalmente",
                f"Liderar equipe de {self.fake.word().title()}"
            ]
        }
        
        return {
            "objetivo_principal": objetivo_principal,
            "objetivos_especificos": random.sample(objetivos_especificos, random.randint(3, 5)),
            "metas_temporais": metas_temporais
        }

    def _generate_habilidades_competencias(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera habilidades e competências."""
        num_tecnicas = random.randint(3, 6)
        num_comportamentais = random.randint(4, 7)
        
        tecnicas = random.sample(self.habilidades_tecnicas, num_tecnicas)
        comportamentais = random.sample(self.habilidades_comportamentais, num_comportamentais)
        
        experiencias = [
            "Projetos acadêmicos",
            "Trabalho voluntário",
            "Estágio",
            "Freelance",
            "Projetos pessoais"
        ]
        
        return {
            "tecnicas": tecnicas,
            "comportamentais": comportamentais,
            "experiencias_relevantes": random.sample(experiencias, random.randint(2, 4))
        }

    def _generate_preferencias_aprendizado(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera preferências de aprendizado."""
        modalidades = ["pratica", "teorica", "mista", "orientada"]
        ritmos = ["acelerado", "moderado", "gradual", "flexivel"]
        horarios = ["manha", "tarde", "noite", "fins de semana", "flexivel"]
        
        recursos = [
            "vídeos", "textos", "exercícios práticos", "projetos", "mentoria",
            "comunidade", "certificações", "livros", "podcasts", "webinars"
        ]
        
        dificuldades = [
            "falta de tempo", "recursos limitados", "teoria abstrata",
            "falta de prática", "isolamento", "falta de feedback"
        ]
        
        return {
            "modalidade_preferida": random.choice(modalidades),
            "ritmo_aprendizado": random.choice(ritmos),
            "horario_estudo": random.choice(horarios),
            "recursos_preferidos": random.sample(recursos, random.randint(3, 6)),
            "dificuldades_aprendizado": random.sample(dificuldades, random.randint(1, 3))
        }

    def _generate_aspiracoes_profissionais(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera aspirações profissionais."""
        salarios = ["2000-3000", "3000-5000", "5000-8000", "8000-12000", "12000+"]
        empresas = ["startup", "multinacional", "empresa média", "ONG", "governo", "freelance"]
        equipes = ["pequena", "média", "grande", "remota", "híbrida"]
        impactos = ["pessoal", "social", "empresarial", "global"]
        
        return {
            "area_interesse": random.choice(self.areas_interesse),
            "salario_desejado": random.choice(salarios),
            "tipo_empresa": random.choice(empresas),
            "tamanho_equipe": random.choice(equipes),
            "impacto_desejado": random.choice(impactos),
            "crescimento_carreira": random.choice(["rápido", "moderado", "gradual"]),
            "equilibrio_vida": random.choice(["importante", "moderado", "secundário"])
        }

    def _generate_barreiras_desafios(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera barreiras e desafios."""
        barreiras_tecnicas = [
            "falta de experiência prática", "conhecimento limitado de ferramentas",
            "dificuldade com tecnologia", "falta de projetos para portfólio"
        ]
        
        barreiras_sociais = [
            "networking limitado", "falta de mentores", "isolamento profissional",
            "falta de referências", "dificuldade de comunicação"
        ]
        
        barreiras_financeiras = [
            "recursos limitados para cursos", "equipamentos", "certificações caras",
            "falta de investimento em educação"
        ]
        
        barreiras_geograficas = [
            "oportunidades limitadas na região", "falta de empresas locais",
            "necessidade de mudança", "concorrência alta"
        ]
        
        return {
            "tecnicas": random.sample(barreiras_tecnicas, random.randint(1, 3)),
            "sociais": random.sample(barreiras_sociais, random.randint(1, 3)),
            "financeiras": random.sample(barreiras_financeiras, random.randint(1, 2)),
            "geograficas": random.sample(barreiras_geograficas, random.randint(1, 2))
        }

    def _generate_interesses_pessoais(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera interesses pessoais."""
        hobbies = [
            "música", "esportes", "leitura", "cinema", "jogos", "culinária",
            "fotografia", "viagem", "arte", "dança", "teatro", "natureza"
        ]
        
        areas_curiosidade = random.sample(self.areas_interesse, random.randint(3, 6))
        
        atividades = [
            "voluntariado", "grupos de estudo", "comunidades online",
            "eventos profissionais", "cursos livres", "workshops"
        ]
        
        midia = [
            "YouTube educativo", "podcasts", "blogs técnicos", "livros",
            "documentários", "cursos online", "newsletters"
        ]
        
        return {
            "hobbies": random.sample(hobbies, random.randint(2, 4)),
            "areas_curiosidade": areas_curiosidade,
            "atividades_extracurriculares": random.sample(atividades, random.randint(1, 3)),
            "consumo_midia": random.sample(midia, random.randint(2, 4))
        }

    def _generate_contexto_socioeconomico(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera contexto socioeconômico."""
        origens = [
            "Cidade grande", "Interior", "Região metropolitana", "Capital",
            "Zona rural", "Periferia", "Centro urbano"
        ]
        
        situacoes = [
            "Classe média", "Classe média baixa", "Classe alta", "Bolsa de estudos",
            "Orçamento limitado", "Recursos moderados", "Boa condição financeira"
        ]
        
        acessos = [
            "Básico", "Moderado", "Bom", "Excelente", "Limitado", "Avançado"
        ]
        
        redes = [
            "Principalmente local", "Regional", "Nacional", "Internacional",
            "Limitada", "Ampla", "Profissional"
        ]
        
        return {
            "origem": random.choice(origens),
            "situacao_financeira": random.choice(situacoes),
            "acesso_tecnologia": random.choice(acessos),
            "rede_social": random.choice(redes)
        }

    def _generate_perfil_disc(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera perfil DISC."""
        perfil_principal = random.choice(self.perfis_disc)
        
        caracteristicas = {
            "Alto D": ["Orientado a resultados", "Decisivo", "Competitivo"],
            "Alto I": ["Comunicativo", "Inspirador", "Sociável"],
            "Alto S": ["Estável", "Paciente", "Colaborativo"],
            "Alto C": ["Analítico", "Preciso", "Sistemático"]
        }
        
        # Seleciona características baseadas no perfil principal
        caracteristicas_chave = []
        for estilo in perfil_principal.split(" - "):
            if estilo in caracteristicas:
                caracteristicas_chave.extend(caracteristicas[estilo])
        
        estilos_comunicacao = {
            "Alto D": "Direta e objetiva",
            "Alto I": "Inspiradora e motivadora",
            "Alto S": "Paciente e colaborativa",
            "Alto C": "Detalhada e precisa"
        }
        
        estilos_lideranca = {
            "Alto D": "Autoritária e decisiva",
            "Alto I": "Inspiradora e motivadora",
            "Alto S": "Colaborativa e inclusiva",
            "Alto C": "Sistemática e organizada"
        }
        
        motivacoes = {
            "Alto D": "Resultados e conquistas",
            "Alto I": "Reconhecimento e interação",
            "Alto S": "Estabilidade e harmonia",
            "Alto C": "Qualidade e precisão"
        }
        
        return {
            "perfil_principal": perfil_principal,
            "caracteristicas_chave": caracteristicas_chave[:4],  # Limita a 4
            "estilo_trabalho": {
                "comunicacao": random.choice(list(estilos_comunicacao.values())),
                "lideranca": random.choice(list(estilos_lideranca.values())),
                "motivacao": random.choice(list(motivacoes.values()))
            },
            "areas_compatibilidade": random.sample(self.areas_interesse, random.randint(3, 5)),
            "pontos_atencao": [
                "Pode precisar de mais paciência",
                "Necessita de feedback constante",
                "Gosta de autonomia"
            ]
        }

    def _generate_talentos_cliftonstrengths(self, perfil_tipo: str) -> Dict[str, Any]:
        """Gera talentos CliftonStrengths."""
        talentos_dominantes = random.sample(self.talentos_clifton, 3)
        talentos_secundarios = random.sample(
            [t for t in self.talentos_clifton if t not in talentos_dominantes], 2
        )
        talentos_desenvolvimento = random.sample(
            [t for t in self.talentos_clifton if t not in talentos_dominantes + talentos_secundarios], 2
        )
        
        return {
            "talentos_dominantes": talentos_dominantes,
            "talentos_secundarios": talentos_secundarios,
            "talentos_desenvolvimento": talentos_desenvolvimento
        }

    def generate_user_batch(self, num_users: int = 100) -> List[Dict[str, Any]]:
        """Gera um lote de usuários com diversidade."""
        users = []
        
        # Tipos de perfil para diversificar
        perfil_tipos = ["universitario", "profissional", "iniciante", "mudanca_carreira", "aleatorio"]
        contextos = ["tecnologia", "negocios", "criatividade", "saude", "educacao", None]
        
        for i in range(num_users):
            perfil_tipo = random.choice(perfil_tipos)
            contexto = random.choice(contextos)
            
            user = self.generate_user(perfil_tipo, contexto)
            users.append(user)
        
        return users

    def save_users(self, users: List[Dict[str, Any]], filename: str = "generated_users.json"):
        """Salva os usuários gerados em arquivo JSON."""
        filepath = f"/Users/pablo.giordani/Documents/repo-pg/my-agents/leve-agents/files/snapshots/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        
        print(f"{len(users)} usuários salvos em {filepath}")

if __name__ == "__main__":
    generator = UserGenerator()
    
    # Gera 150 usuários diversificados
    print("Gerando usuários diversificados...")
    users = generator.generate_user_batch(150)
    
    # Salva os usuários
    generator.save_users(users, "generated_users_extended.json")
    
    print(f"Estatísticas dos usuários gerados:")
    print(f"   - Total: {len(users)}")
    
    # Conta por perfil DISC
    disc_profiles = {}
    for user in users:
        disc = user['perfil_disc']['perfil_principal']
        disc_profiles[disc] = disc_profiles.get(disc, 0) + 1
    
    print("   - Perfis DISC mais comuns:")
    for disc, count in sorted(disc_profiles.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"     {disc}: {count}")
    
    print("✨ Geração concluída!")
