"""
generate_json.py
Generates data/politicos.json from hardcoded candidate data.
"""

import json
import os

# ---------------------------------------------------------------------------
# Party mapping: partyId (UUID) → acronym
# ---------------------------------------------------------------------------
PARTIES = {
    "3f7a519d-641b-4b56-95df-dcb4cc51cad1": "Republicanos",
    "708310c7-1f6c-4b94-bfff-0c054f8cd23c": "PP",
    "bd4e73ca-5d10-412d-b8e5-0c7c60be9129": "PDT",
    "2c7ac784-e2d0-4f39-a9bc-7b304cef80ba": "PT",
    "e4073f74-db47-4fc0-b753-76578da1b984": "Missão",
    "78dc85ea-eeca-4b75-b4e9-df5dfa458e59": "MDB",
    "36be010b-0aca-4e17-96ad-7e07444b5096": "PSTU",
    "8697f453-2322-44b6-9e12-ea0b20e55458": "Rede",
    "afa9277d-2976-455e-a29f-c13972eba793": "Podemos",
    "33523bb5-8417-4e69-8a44-f0830f6ac205": "PCB",
    "3cd8d415-938d-4ec3-9380-953d393cc334": "PL",
    "f93753ed-2216-4a43-b9c8-a8e113d9c9a5": "Cidadania",
    "99114c4e-43b2-40a2-810d-94c159f8822d": "PRD",
    "2f016de3-b59e-480b-bac8-6569e5964bbf": "DC",
    "33c86dbc-f744-471a-9c9c-c5789c8cb929": "PRTB",
    "4c7c6b3a-f1ee-4d56-bc1a-05c6f27723ad": "PCO",
    "0284074c-12c9-4075-9852-f661fefe5b10": "Novo",
    "320fa8c4-a3a8-442e-a071-343434b4775e": "Mobiliza",
    "d40b9e69-3c17-427a-ae36-cf35149740d3": "Democrata",
    "b27fd6a1-3f0f-49e4-90fc-eba13a5abda0": "Agir",
    "6d30dafa-5c4f-4b51-94c3-e224b6b7fc41": "PSB",
    "7d8418ea-cfa5-4bb8-9f5d-9bdd857e521d": "PV",
    "821fa0bf-01d9-4a28-9d9a-549cf9404e9f": "União",
    "679fbefd-be34-4302-b144-282bd8dedeb1": "PSDB",
    "ca1a706f-58e3-4ebd-9958-007e087766a0": "PSOL",
    "58333878-307a-4685-af05-498e3551c5a5": "PSD",
    "f03e1dd1-9d68-44b6-b292-b5c9e6750671": "PC do B",
    "8f607ae4-b877-437e-9fa2-62832275f79b": "Avante",
    "c3293632-81f2-48f1-82c2-3ad8892ba991": "Solidariedade",
    "860b1a2d-d0c7-4ca0-9c3c-7079696fd732": "UP",
    "49b454c3-0aab-4c19-98c5-ca7759fd0c8f": "PSL",
}

# ---------------------------------------------------------------------------
# Candidate tuples:
# (tseCandidateId, ballotName, fullName, state, office, number, partyId,
#  totalAssets, photoUrl, education, occupation, gender, race,
#  coalitionName, uuid, result_dict)
# ---------------------------------------------------------------------------
CANDIDATES = [
    # Presidential candidates
    (280002551544, "FLAVIO BOLSONARO", "FLAVIO NANTES BOLSONARO", "BR", "presidente", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 8186555.83, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002551544/BR", "SUPERIOR COMPLETO", "SENADOR", "MASCULINO", "BRANCA", "PARTIDO ISOLADO", "a41148b9-d409-461e-b1fd-76eb0cf44931", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 56104503, "voteShare": 47.03, "final": True}),
    (280002542548, "LULA", "LUIZ INÁCIO LULA DA SILVA", "BR", "presidente", 13, "2c7ac784-e2d0-4f39-a9bc-7b304cef80ba", 4775650.64, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002542548/BR", "ENSINO FUNDAMENTAL COMPLETO", "TORNEIRO MECÂNICO", "MASCULINO", "BRANCA", "BRASIL PRONTO PRA MAIS", "0ffaf29a-23e7-41d2-8663-5f35080119f8", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 53879538, "voteShare": 45.16, "final": True}),
    (280002551547, "ESCRITOR AUGUSTO CURY", "AUGUSTO JORGE CURY", "BR", "presidente", 70, "8f607ae4-b877-437e-9fa2-62832275f79b", 242593012.43, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002551547/BR", "SUPERIOR COMPLETO", "ESCRITOR E CRÍTICO", "MASCULINO", "BRANCA", "BRASIL DOS NOSSOS SONHOS", "e02019ef-2443-4e80-ab11-411e8208c0aa", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 3448569, "voteShare": 2.89, "final": True}),
    (280002551932, "RONALDO CAIADO", "RONALDO RAMOS CAIADO", "BR", "presidente", 55, "58333878-307a-4685-af05-498e3551c5a5", 52557930.98, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002551932/BR", "SUPERIOR COMPLETO", "MÉDICO", "MASCULINO", "BRANCA", "PARTIDO ISOLADO", "9f9b2699-a849-4101-9050-90e3ee2a0ef5", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 2605148, "voteShare": 2.18, "final": True}),
    (280002540694, "RENAN SANTOS", "RENAN ANTONIO FERREIRA DOS SANTOS", "BR", "presidente", 14, "e4073f74-db47-4fc0-b753-76578da1b984", 795089, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002540694/BR", "SUPERIOR INCOMPLETO", "EMPRESÁRIO", "MASCULINO", "BRANCA", "PARTIDO ISOLADO", "062de96d-b021-4127-b851-0b3871c10a72", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 2675887, "voteShare": 2.24, "final": True}),
    (280002539826, "ZEMA", "ROMEU ZEMA NETO", "BR", "presidente", 30, "0284074c-12c9-4075-9852-f661fefe5b10", 178707610.09, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002539826/BR", "SUPERIOR COMPLETO", "EMPRESÁRIO", "MASCULINO", "BRANCA", "PARTIDO ISOLADO", "616aa68d-6999-47d7-90f5-3cc5443cc46b", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 326488, "voteShare": 0.27, "final": True}),
    (280002538811, "SAMARA", "SAMARA MARTINS DA SILVA FEITOSA", "BR", "presidente", 80, "860b1a2d-d0c7-4ca0-9c3c-7079696fd732", 33000, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002538811/BR", "SUPERIOR COMPLETO", "ODONTÓLOGO", "FEMININO", "PRETA", "PARTIDO ISOLADO", "71a04f7e-6430-4b1f-b2a2-e0756e9d1ffa", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 122911, "voteShare": 0.10, "final": True}),
    (280002551975, "EDMILSON COSTA", "EDMILSON SILVA COSTA", "BR", "presidente", 21, "33523bb5-8417-4e69-8a44-f0830f6ac205", 454485.68, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002551975/BR", "SUPERIOR COMPLETO", "APOSENTADO", "MASCULINO", "PARDA", "PARTIDO ISOLADO", "b6383eaf-1384-4ef5-96bd-f9e2abb6d2f1", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 22693, "voteShare": 0.02, "final": True}),
    (280002541457, "HERTZ DIAS", "HERTZ DA CONCEICAO DIAS", "BR", "presidente", 16, "36be010b-0aca-4e17-96ad-7e07444b5096", 170000, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002541457/BR", "SUPERIOR COMPLETO", "PROFESSOR", "MASCULINO", "PRETA", "PARTIDO ISOLADO", "e939da2f-e34b-4649-b848-8b64d95de99d", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 43103, "voteShare": 0.04, "final": True}),
    (280002552487, "RUI COSTA PIMENTA", "RUI COSTA PIMENTA", "BR", "presidente", 29, "4c7c6b3a-f1ee-4d56-bc1a-05c6f27723ad", 0, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002552487/BR", "SUPERIOR COMPLETO", "JORNALISTA E REDATOR", "MASCULINO", "BRANCA", "PARTIDO ISOLADO", "5a294685-041d-4b4c-9720-f4d1c8f7614b", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 15024, "voteShare": 0.01, "final": True}),
    (280002552484, "CLARIANA BARAO", "CLARIANA ZACARKIM BARAO", "BR", "presidente", 27, "2f016de3-b59e-480b-bac8-6569e5964bbf", 1820760.17, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002552484/BR", "SUPERIOR COMPLETO", "ADVOGADO", "FEMININO", "BRANCA", "PARTIDO ISOLADO", "861b8995-aca9-4a46-9e2d-956fd4ba2bb8", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 40043, "voteShare": 0.03, "final": True}),
    (280002548139, "VETERINÁRIO WILSON GRASSI", "WILSON GRASSI JUNIOR", "BR", "presidente", 35, "d40b9e69-3c17-427a-ae36-cf35149740d3", 50000000, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/280002548139/BR", "SUPERIOR COMPLETO", "VETERINÁRIO", "MASCULINO", "BRANCA", "PARTIDO ISOLADO", "9adf69b5-9092-468b-a8e8-fd6714719a3e", {"round": 1, "status": "Não eleito", "outcome": "notElected", "votes": 16881, "voteShare": 0.01, "final": True}),

    # Governors elected in 1st round
    (110002551480, "OTAVIANO PIVETTA", "OTAVIANO OLAVO PIVETTA", "MT", "governador", 10, "3f7a519d-641b-4b56-95df-dcb4cc51cad1", 575680870.95, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/110002551480/MT", "ENSINO FUNDAMENTAL COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "MATO GROSSO NÃO PODE PARAR", "4a5cb2aa-a306-4aee-b3a5-016c5d11b5ac", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 1128099, "voteShare": 60.77, "final": True}),
    (120002536582, "EDUARDO RIEDEL", "EDUARDO CORREA RIEDEL", "MS", "governador", 11, "708310c7-1f6c-4b94-bfff-0c054f8cd23c", 16147849.34, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/120002536582/MS", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "FAZENDO O FUTURO ACONTECER", "32be1e2f-4cd8-4fae-8888-3f739fbc6c46", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 914323, "voteShare": 67.07, "final": True}),
    (90002540993, "DANIEL VILELA", "DANIEL ELIAS CARVALHO VILELA", "GO", "governador", 15, "78dc85ea-eeca-4b75-b4e9-df5dfa458e59", 5627385.99, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/90002540993/GO", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "PRA GOIÁS SEGUIR EM FRENTE", "74e43450-99fc-4c2d-a784-349d1b3c37aa", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 2148218, "voteShare": 59.17, "final": True}),
    (140002549930, "DR. DANIEL", "DANIEL BARBOSA SANTOS", "PA", "governador", 20, "afa9277d-2976-455e-a29f-c13972eba793", 4753760.8, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/140002549930/PA", "SUPERIOR COMPLETO", "MÉDICO", "MASCULINO", "PARDA", "O PARÁ É DO POVO!", "36cbafb0-7dbf-4dd0-8204-0a1a703d164c", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 2345721, "voteShare": 51.40, "final": True}),
    (240002537073, "JORGINHO MELLO", "JORGINHO DOS SANTOS MELLO", "SC", "governador", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 2818036.89, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/240002537073/SC", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "FÉ NO TRABALHO", "56b4cd53-b29c-470e-b554-b6e0f4b36083", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 2942386, "voteShare": 68.98, "final": True}),
    (250002541303, "TARCÍSIO", "TARCISIO GOMES DE FREITAS", "SP", "governador", 10, "3f7a519d-641b-4b56-95df-dcb4cc51cad1", 2696808.40, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/250002541303/SP", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "CORAGEM PARA SEGUIR", "0db50ca0-30bd-4a75-ab20-b2a812a678aa", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 14491874, "voteShare": 62.65, "final": True}),
    (220002541939, "MARCOS ROGÉRIO", "MARCOS ROGERIO DA SILVA BRITO", "RO", "governador", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 2376169.92, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/220002541939/RO", "SUPERIOR COMPLETO", "SENADOR", "MASCULINO", "PARDA", "JUNTOS POR RONDÔNIA", "2bf2db3b-2c98-4dd5-a576-9dd47a33bbd8", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 537370, "voteShare": 56.86, "final": True}),
    (20002553350, "JHC", "JOÃO HENRIQUE HOLANDA CALDAS", "AL", "governador", 45, "679fbefd-be34-4302-b144-282bd8dedeb1", 2244732.19, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/20002553350/AL", "SUPERIOR COMPLETO", "ADVOGADO", "MASCULINO", "PARDA", "ALAGOAS GIGANTE", "beaf8510-70ca-4eea-ad1e-e7d7870665dd", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 892484, "voteShare": 52.19, "final": True}),
    (180002532987, "RAFAEL FONTELES", "RAFAEL TAJRA FONTELES", "PI", "governador", 13, "2c7ac784-e2d0-4f39-a9bc-7b304cef80ba", 1799948.60, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/180002532987/PI", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "A FORÇA DO POVO", "0d3b3e4d-2c9d-44e7-b002-fb44e67c3764", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 1436697, "voteShare": 70.90, "final": True}),
    (260002542491, "FÁBIO", "FABIO CRUZ MITIDIERI", "SE", "governador", 55, "58333878-307a-4685-af05-498e3551c5a5", 1698945.66, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/260002542491/SE", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "SERGIPE CRESCE COM VOCÊ", "443c0581-fe10-4dbd-b29a-5d02417160cc", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 727291, "voteShare": 59.27, "final": True}),
    (30002530014, "DR. FURLAN", "ANTONIO PAULO DE OLIVEIRA FURLAN", "AP", "governador", 55, "58333878-307a-4685-af05-498e3551c5a5", 1168464.77, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/30002530014/AP", "SUPERIOR COMPLETO", "MÉDICO", "MASCULINO", "BRANCA", "TRABALHAR PARA TRANSFORMAR", "53f80599-310a-4f82-9896-604ab765dfd8", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 281595, "voteShare": 62.75, "final": True}),
    (100002545679, "EDUARDO BRAIDE", "EDUARDO SALIM BRAIDE", "MA", "governador", 55, "58333878-307a-4685-af05-498e3551c5a5", 1048910.76, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/100002545679/MA", "SUPERIOR COMPLETO", "ADVOGADO", "MASCULINO", "BRANCA", "PRA TRANSFORMAR O MARANHÃO", "2e59cfa0-05c8-4612-b2f6-03c6306bd96b", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 2104122, "voteShare": 54.08, "final": True}),
    (160002540833, "SERGIO MORO", "SERGIO FERNANDO MORO", "PR", "governador", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 1036642.25, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/160002540833/PR", "SUPERIOR COMPLETO", "SENADOR", "MASCULINO", "BRANCA", "FORTALEZA PARANÁ", "1c1eff8c-79b9-4317-9a97-c634fb6137b3", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 3127911, "voteShare": 50.10, "final": True}),
    (130002552296, "CLEITINHO AZEVEDO", "CLEITON GONTIJO DE AZEVEDO", "MG", "governador", 10, "3f7a519d-641b-4b56-95df-dcb4cc51cad1", 956564.03, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/130002552296/MG", "ENSINO FUNDAMENTAL COMPLETO", "SENADOR", "MASCULINO", "BRANCA", "MINAS É DO POVO", "1450ec25-3dbc-4ee6-a121-a15c00e21599", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 6321590, "voteShare": 55.40, "final": True}),
    (50002536314, "JERÔNIMO RODRIGUES", "JERONIMO RODRIGUES SOUZA", "BA", "governador", 13, "2c7ac784-e2d0-4f39-a9bc-7b304cef80ba", 886548.53, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/50002536314/BA", "SUPERIOR COMPLETO", "SERVIDOR PÚBLICO ESTADUAL", "MASCULINO", "INDÍGENA", "MAIS BAHIA, MAIS BRASIL", "8d7c4311-1694-4a3d-870c-a8a6488f486b", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 4626509, "voteShare": 55.70, "final": True}),
    (150002551789, "LUCAS RIBEIRO", "LUCAS RIBEIRO NOVAIS DE ARAUJO", "PB", "governador", 11, "708310c7-1f6c-4b94-bfff-0c054f8cd23c", 741354.91, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/150002551789/PB", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "DAQUI PRA MELHOR", "3d919991-0b6c-40f4-a40b-d362b0415498", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 1470252, "voteShare": 64.30, "final": True}),
    (210002547857, "ZUCCO", "LUCIANO LORENZINI ZUCCO", "RS", "governador", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 709304, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/210002547857/RS", "SUPERIOR COMPLETO", "DEPUTADO", "MASCULINO", "BRANCA", "O RIO GRANDE PODE MAIS", "128bf8a5-bfaf-4f72-a7f6-654bb028a935", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 3516048, "voteShare": 58.05, "final": True}),
    (230002549223, "ARTHUR HENRIQUE", "ARTHUR HENRIQUE BRANDAO MACHADO", "RR", "governador", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 578525.64, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/230002549223/RR", "SUPERIOR INCOMPLETO", "OUTROS", "MASCULINO", "PARDA", "UNIDOS POR RORAIMA", "e211e40a-4125-42e1-be07-0aaf28fd9205", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 220809, "voteShare": 69.13, "final": True}),
    (60002543969, "ELMANO DE FREITAS", "ELMANO DE FREITAS DA COSTA", "CE", "governador", 13, "2c7ac784-e2d0-4f39-a9bc-7b304cef80ba", 366457.71, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/60002543969/CE", "SUPERIOR COMPLETO", "GOVERNADOR", "MASCULINO", "PARDA", "CEARÁ FORTE", "ea381cee-b572-459b-8106-2d9ac413945d", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 2875573, "voteShare": 53.14, "final": True}),
    (170002537227, "RAQUEL LYRA", "RAQUEL TEIXEIRA LYRA LUCENA", "PE", "governador", 55, "58333878-307a-4685-af05-498e3551c5a5", 359498.33, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/170002537227/PE", "SUPERIOR COMPLETO", "GOVERNADOR", "FEMININO", "BRANCA", "PERNAMBUCO DE CORAÇÃO", "d2d50ee0-171a-43bc-9e95-96a93009fb4d", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 2805438, "voteShare": 53.27, "final": True}),
    (190002542887, "DOUGLAS RUAS", "DOUGLAS RUAS DOS SANTOS", "RJ", "governador", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 1467687.88, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/190002542887/RJ", "SUPERIOR COMPLETO", "DEPUTADO", "MASCULINO", "BRANCA", "RIO REAL", "b49f2678-d5fc-45e7-950d-cfa82912edf0", {"round": 1, "status": "Eleito", "outcome": "elected", "votes": 4271199, "voteShare": 50.88, "final": True}),

    # Governor runoff candidates
    (10002544107, "MAILZA ASSIS", "MAILZA ASSIS CAMELI", "AC", "governador", 11, "708310c7-1f6c-4b94-bfff-0c054f8cd23c", 167482.91, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/10002544107/AC", "SUPERIOR COMPLETO", "GOVERNADOR", "FEMININO", "BRANCA", "AVANÇA ACRE", "37ff270b-70ec-4ed3-9b6c-848ad3784018", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 218760, "voteShare": 49.76, "final": True}),
    (10002532492, "ALAN RICK", "ALAN RICK MIRANDA", "AC", "governador", 10, "3f7a519d-641b-4b56-95df-dcb4cc51cad1", 5244567.72, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/10002532492/AC", "SUPERIOR COMPLETO", "JORNALISTA E REDATOR", "MASCULINO", "BRANCA", "TRABALHO DA ESPERANÇA", "e487b05e-2575-4f8b-ae97-789f785ed2d7", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 141859, "voteShare": 32.27, "final": True}),
    (40002532272, "OMAR AZIZ", "OMAR JOSE ABDELAZIZ", "AM", "governador", 55, "58333878-307a-4685-af05-498e3551c5a5", 2070608.0, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/40002532272/AM", "SUPERIOR COMPLETO", "SENADOR", "MASCULINO", "BRANCA", "FORÇA AMAZONAS", "6ad4feec-a4b8-442e-9353-74f6ba670a37", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 841846, "voteShare": 40.56, "final": True}),
    (40002541626, "PROFESSORA MARIA DO CARMO", "MARIA DO CARMO SEFFAIR LINS DE ALBUQUERQUE", "AM", "governador", 22, "3cd8d415-938d-4ec3-9380-953d393cc334", 118473769.48, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/40002541626/AM", "SUPERIOR COMPLETO", "EMPRESÁRIO", "FEMININO", "BRANCA", "MUDAR É URGENTE", "f4231d42-7172-4d70-a511-9c683c0b7a8d", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 507335, "voteShare": 24.57, "final": True}),
    (70002553055, "CELINA LEÃO", "CELINA LEAO HIZIM FERREIRA", "DF", "governador", 11, "708310c7-1f6c-4b94-bfff-0c054f8cd23c", 440131.39, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/70002553055/DF", "SUPERIOR COMPLETO", "GOVERNADOR", "FEMININO", "BRANCA", "PROPÓSITO E AÇÃO", "a9a981ad-d212-41d7-b97d-2b78a8ab3577", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 825530, "voteShare": 49.93, "final": True}),
    (70002552496, "LEANDRO GRASS", "LEANDRO ANTÔNIO GRASS PEIXOTO", "DF", "governador", 13, "2c7ac784-e2d0-4f39-a9bc-7b304cef80ba", 285000, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/70002552496/DF", "SUPERIOR COMPLETO", "PROFESSOR DE ENSINO SUPERIOR", "MASCULINO", "BRANCA", "DF DO POVO", "9529ca34-374c-45ec-bb47-cfe6a10e49d3", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 569930, "voteShare": 34.47, "final": True}),
    (80002552682, "LORENZO PAZOLINI", "LORENZO SILVA DE PAZOLINI", "ES", "governador", 10, "3f7a519d-641b-4b56-95df-dcb4cc51cad1", 1002342.77, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/80002552682/ES", "SUPERIOR COMPLETO", "SERVIDOR PÚBLICO ESTADUAL", "MASCULINO", "BRANCA", "PAZ PRA VIVER", "265e0925-a7c9-4279-b2cb-d988d40aeb87", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 1048633, "voteShare": 49.65, "final": True}),
    (80002552172, "RICARDO FERRAÇO", "RICARDO DE REZENDE FERRAÇO", "ES", "governador", 15, "78dc85ea-eeca-4b75-b4e9-df5dfa458e59", 27668789.55, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/80002552172/ES", "SUPERIOR INCOMPLETO", "GOVERNADOR", "MASCULINO", "BRANCA", "AGORA É O FUTURO", "add1f697-cc23-4bcd-ab17-8917530739f5", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 719397, "voteShare": 34.06, "final": True}),
    (200002535255, "ALLYSON", "ALLYSON LEANDRO BEZERRA SILVA", "RN", "governador", 44, "821fa0bf-01d9-4a28-9d9a-549cf9404e9f", 748869.84, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/200002535255/RN", "SUPERIOR COMPLETO", "SERVIDOR PÚBLICO FEDERAL", "MASCULINO", "PARDA", "ESPERANÇA E TRABALHO", "89d68d5b-4676-49aa-b344-32d42adeb2a6", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 733809, "voteShare": 36.94, "final": True}),
    (200002534001, "CADU DE LULA", "CARLOS EDUARDO XAVIER", "RN", "governador", 13, "2c7ac784-e2d0-4f39-a9bc-7b304cef80ba", 100000, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/200002534001/RN", "SUPERIOR COMPLETO", "ENGENHEIRO", "MASCULINO", "BRANCA", "TIME QUE CUIDA", "4475a786-b629-41ef-8c9b-77dd1a3dfb47", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 718300, "voteShare": 36.16, "final": True}),
    (270002544544, "VICENTINHO JÚNIOR", "VICENTE ALVES DE OLIVEIRA JÚNIOR", "TO", "governador", 45, "679fbefd-be34-4302-b144-282bd8dedeb1", 3983398, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/270002544544/TO", "ENSINO MÉDIO COMPLETO", "DEPUTADO", "MASCULINO", "PARDA", "PRA CIMA TOCANTINS", "9e71ecc0-ad90-4d9e-807d-adcfcedc089e", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 372848, "voteShare": 43.94, "final": True}),
    (270002544599, "PROFESSORA DORINHA", "MARIA AUXILIADORA SEABRA REZENDE", "TO", "governador", 44, "821fa0bf-01d9-4a28-9d9a-549cf9404e9f", 2352740.28, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/270002544599/TO", "SUPERIOR COMPLETO", "SENADOR", "FEMININO", "BRANCA", "UNIÃO PELO TOCANTINS", "c220b966-8870-4335-a301-4b050c4345f4", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 386260, "voteShare": 45.52, "final": True}),
    (190002543380, "EDUARDO PAES", "EDUARDO DA COSTA PAES", "RJ", "governador", 55, "58333878-307a-4685-af05-498e3551c5a5", 189210.63, "https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/20322002026/190002543380/RJ", "SUPERIOR COMPLETO", "OUTROS", "MASCULINO", "BRANCA", "JUNTOS PARA MUDAR", "b51f1ae9-cfe8-453f-9d39-a7356134fc13", {"round": 1, "status": "2º turno", "outcome": "runoff", "votes": 3706984, "voteShare": 42.76, "final": True}),
]

# ---------------------------------------------------------------------------
# Filings (candidaturas anteriores)
# key: str(tseCandidateId)
# ---------------------------------------------------------------------------
FILINGS = {
    "280002551544": [  # Flávio Bolsonaro
        {"ano": 2006, "cargo": "DEPUTADO ESTADUAL", "estado": "RJ", "partido": "PP", "bens": 385000},
        {"ano": 2010, "cargo": "DEPUTADO ESTADUAL", "estado": "RJ", "partido": "PP", "bens": 690978.23},
        {"ano": 2014, "cargo": "DEPUTADO ESTADUAL", "estado": "RJ", "partido": "PP", "bens": 714394.69},
        {"ano": 2016, "cargo": "PREFEITO", "estado": "RJ", "partido": "PROS", "bens": 1454218.06},
        {"ano": 2018, "cargo": "SENADOR", "estado": "RJ", "partido": "PSL", "bens": 1741758.15},
        {"ano": 2026, "cargo": "PRESIDENTE", "estado": "BR", "partido": "PL", "bens": 8186555.83},
    ],
    "280002542548": [  # Lula
        {"ano": 2006, "cargo": "PRESIDENTE", "estado": "BR", "partido": "PT", "bens": 839033.52},
        {"ano": 2018, "cargo": "PRESIDENTE", "estado": "BR", "partido": "PT", "bens": 7987921.57},
        {"ano": 2022, "cargo": "PRESIDENTE", "estado": "BR", "partido": "PT", "bens": 7423725.78},
        {"ano": 2026, "cargo": "PRESIDENTE", "estado": "BR", "partido": "PT", "bens": 4775650.64},
    ],
}


def build_entry(candidate):
    (
        tseCandidateId, ballotName, fullName, state, office, number, partyId,
        totalAssets, photoUrl, education, occupation, gender, race,
        coalitionName, uuid, result,
    ) = candidate

    resultado = None
    if result is not None:
        resultado = {
            "turno": result["round"],
            "votos": result["votes"],
            "pct": result["voteShare"],
            "situacao": result["status"],
        }

    key = str(tseCandidateId)
    return key, {
        "nome": ballotName.title(),
        "nomeCompleto": fullName,
        "partido": PARTIES[partyId],
        "numero": number,
        "cargo": office,
        "estado": state,
        "foto": photoUrl,
        "totalBens": totalAssets,
        "educacao": education,
        "ocupacao": occupation,
        "genero": gender,
        "raca": race,
        "coligacao": coalitionName,
        "uuid": uuid,
        "resultado": resultado,
        "candidaturas": FILINGS.get(key, []),
    }


def main():
    output = {}
    for candidate in CANDIDATES:
        key, entry = build_entry(candidate)
        output[key] = entry

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "politicos.json",
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Written {len(output)} candidates to {out_path}")
    total_bytes = os.path.getsize(out_path)
    print(f"File size: {total_bytes:,} bytes")


if __name__ == "__main__":
    main()
