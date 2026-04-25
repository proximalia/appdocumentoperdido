// Aplicação Frontend - Achados e Perdidos

// Configuração do Mapa
let map;
let marker;
let selectedLocation = null;

// Inicializar mapa quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadStats();
    loadMatches();
    setupForms();
});

function initMap() {
    // Inicializar mapa centrado no Brasil (São Paulo)
    map = L.map('map').setView([-23.5505, -46.6333], 13);

    // Adicionar camada do OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Adicionar marcador ao clicar no mapa
    map.on('click', function(e) {
        const { lat, lng } = e.latlng;

        // Remover marcador anterior se existir
        if (marker) {
            map.removeLayer(marker);
        }

        // Adicionar novo marcador
        marker = L.marker([lat, lng]).addTo(map);

        // Salvar coordenadas
        selectedLocation = { lat, lng };
        document.getElementById('latitude').value = lat;
        document.getElementById('longitude').value = lng;

        // Feedback visual
        marker.bindPopup('📍 Documento deixado aqui').openPopup();
    });

    // Tentar obter localização do usuário
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const { latitude, longitude } = position.coords;
            map.setView([latitude, longitude], 15);
        });
    }
}

function setupForms() {
    // Form de documento perdido
    document.getElementById('form-perdido').addEventListener('submit', async function(e) {
        e.preventDefault();

        const data = {
            tipo_documento: document.getElementById('tipo-perdido').value,
            numero_documento: document.getElementById('numero-perdido').value,
            nome_documento: document.getElementById('nome-perdido').value,
            cpf_documento: document.getElementById('cpf-perdido').value,
            email: document.getElementById('email-perdido').value,
            descricao: document.getElementById('descricao-perdido').value
        };

        try {
            // Simulação de salvamento (em produção, fazer POST para API)
            console.log('Registrando documento perdido:', data);

            // Salvar no localStorage para demonstração
            let perdidos = JSON.parse(localStorage.getItem('documentos_perdidos') || '[]');
            perdidos.push({
                ...data,
                id: Date.now(),
                data_registro: new Date().toISOString(),
                status: 'perdido'
            });
            localStorage.setItem('documentos_perdidos', JSON.stringify(perdidos));

            alert('✅ Documento perdido registrado com sucesso!\n\nVocê receberá um email se encontrarmos seu documento.');
            this.reset();
            loadStats();

        } catch (error) {
            console.error('Erro:', error);
            alert('❌ Erro ao registrar. Tente novamente.');
        }
    });

    // Form de documento achado
    document.getElementById('form-achado').addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!selectedLocation) {
            alert('⚠️ Por favor, marque no mapa onde você deixou o documento!');
            return;
        }

        const data = {
            tipo_documento: document.getElementById('tipo-achado').value,
            numero_documento: document.getElementById('numero-achado').value,
            nome_documento: document.getElementById('nome-achado').value,
            cpf_documento: document.getElementById('cpf-achado').value,
            email: document.getElementById('email-achado').value,
            local_encontrado: document.getElementById('local-achado').value,
            latitude: selectedLocation.lat,
            longitude: selectedLocation.lng
        };

        try {
            console.log('Registrando documento achado:', data);

            // Salvar no localStorage
            let achados = JSON.parse(localStorage.getItem('documentos_achados') || '[]');
            achados.push({
                ...data,
                id: Date.now(),
                data_registro: new Date().toISOString(),
                status: 'disponivel'
            });
            localStorage.setItem('documentos_achados', JSON.stringify(achados));

            // Processar matches
            processMatches();

            alert('✅ Documento achado registrado com sucesso!\n\nSe encontrarmos o dono, entraremos em contato!');
            this.reset();

            // Limpar mapa
            if (marker) {
                map.removeLayer(marker);
                marker = null;
            }
            selectedLocation = null;

            loadStats();
            loadMatches();

        } catch (error) {
            console.error('Erro:', error);
            alert('❌ Erro ao registrar. Tente novamente.');
        }
    });
}

function calculateSimilarity(str1, str2) {
    if (!str1 || !str2) return 0;

    str1 = str1.toLowerCase();
    str2 = str2.toLowerCase();

    if (str1 === str2) return 100;

    // Algoritmo simples de similaridade
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;

    if (longer.length === 0) return 100;

    const editDistance = (s1, s2) => {
        s1 = s1.toLowerCase();
        s2 = s2.toLowerCase();
        const costs = [];

        for (let i = 0; i <= s1.length; i++) {
            let lastValue = i;
            for (let j = 0; j <= s2.length; j++) {
                if (i === 0) {
                    costs[j] = j;
                } else if (j > 0) {
                    let newValue = costs[j - 1];
                    if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
                        newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
                    }
                    costs[j - 1] = lastValue;
                    lastValue = newValue;
                }
            }
            if (i > 0) costs[s2.length] = lastValue;
        }
        return costs[s2.length];
    };

    return ((longer.length - editDistance(longer, shorter)) / longer.length) * 100;
}

function processMatches() {
    const perdidos = JSON.parse(localStorage.getItem('documentos_perdidos') || '[]');
    const achados = JSON.parse(localStorage.getItem('documentos_achados') || '[]');
    let matches = JSON.parse(localStorage.getItem('matches') || '[]');

    for (const perdido of perdidos) {
        for (const achado of achados) {
            // Verificar se já existe match
            const existingMatch = matches.find(m =>
                m.perdido_id === perdido.id && m.achado_id === achado.id
            );

            if (existingMatch) continue;

            let score = 0;
            let maxScore = 0;

            // Tipo de documento (20 pontos)
            maxScore += 20;
            if (perdido.tipo_documento === achado.tipo_documento) {
                score += 20;
            }

            // Número do documento (40 pontos)
            if (perdido.numero_documento && achado.numero_documento) {
                maxScore += 40;
                if (perdido.numero_documento === achado.numero_documento) {
                    score += 40;
                } else {
                    const numSim = calculateSimilarity(perdido.numero_documento, achado.numero_documento);
                    score += (numSim / 100) * 40;
                }
            }

            // Nome (25 pontos)
            if (perdido.nome_documento && achado.nome_documento) {
                maxScore += 25;
                const nomeSim = calculateSimilarity(perdido.nome_documento, achado.nome_documento);
                score += (nomeSim / 100) * 25;
            }

            // CPF (15 pontos)
            if (perdido.cpf_documento && achado.cpf_documento) {
                maxScore += 15;
                if (perdido.cpf_documento === achado.cpf_documento) {
                    score += 15;
                } else {
                    const cpfSim = calculateSimilarity(perdido.cpf_documento, achado.cpf_documento);
                    score += (cpfSim / 100) * 15;
                }
            }

            // Calcular score final
            const finalScore = maxScore > 0 ? (score / maxScore) * 100 : 0;

            // Se score >= 60%, criar match
            if (finalScore >= 60) {
                matches.push({
                    id: Date.now() + Math.random(),
                    perdido_id: perdido.id,
                    achado_id: achado.id,
                    perdido: perdido,
                    achado: achado,
                    score: Math.round(finalScore),
                    data_match: new Date().toISOString(),
                    notificado: false
                });

                console.log(`🎯 Match encontrado! Score: ${Math.round(finalScore)}%`);
            }
        }
    }

    localStorage.setItem('matches', JSON.stringify(matches));
}

function loadStats() {
    const perdidos = JSON.parse(localStorage.getItem('documentos_perdidos') || '[]');
    const achados = JSON.parse(localStorage.getItem('documentos_achados') || '[]');
    const matches = JSON.parse(localStorage.getItem('matches') || '[]');

    document.getElementById('stat-perdidos').textContent = perdidos.length;
    document.getElementById('stat-achados').textContent = achados.length;
    document.getElementById('stat-matches').textContent = matches.length;
}

function loadMatches() {
    const matches = JSON.parse(localStorage.getItem('matches') || '[]');
    const container = document.getElementById('matches-container');

    if (matches.length === 0) {
        container.innerHTML = `
            <p style="color: #999; text-align: center; padding: 20px;">
                Nenhuma correspondência ainda. O sistema monitora automaticamente e enviará email quando encontrar um match!
            </p>
        `;
        return;
    }

    container.innerHTML = matches.map(match => `
        <div class="match-card">
            <span class="match-score">Match: ${match.score}%</span>
            <div class="match-info">
                <p><strong>📄 Tipo:</strong> ${match.perdido.tipo_documento}</p>
                <p><strong>👤 Nome:</strong> ${match.perdido.nome_documento}</p>
                <p><strong>📧 Email do dono:</strong> ${match.perdido.email}</p>
                <p><strong>📍 Localização do documento:</strong> ${match.achado.local_encontrado}</p>
                <p><strong>🗺️ Coordenadas:</strong> ${match.achado.latitude.toFixed(6)}, ${match.achado.longitude.toFixed(6)}</p>
                <p><strong>📅 Encontrado em:</strong> ${new Date(match.data_match).toLocaleDateString('pt-BR')}</p>
                <button onclick="showOnMap(${match.achado.latitude}, ${match.achado.longitude})"
                        style="margin-top: 10px; width: auto; padding: 10px 20px;">
                    🗺️ Ver no Mapa
                </button>
            </div>
        </div>
    `).join('');
}

function showOnMap(lat, lng) {
    // Scroll para o mapa
    document.getElementById('map').scrollIntoView({ behavior: 'smooth' });

    // Centralizar e fazer zoom no local
    map.setView([lat, lng], 17);

    // Adicionar marcador temporário
    const tempMarker = L.marker([lat, lng])
        .addTo(map)
        .bindPopup('📍 Documento está aqui!')
        .openPopup();

    // Remover marcador após 5 segundos
    setTimeout(() => {
        if (tempMarker && map.hasLayer(tempMarker)) {
            map.removeLayer(tempMarker);
        }
    }, 5000);
}

// Atualizar stats a cada 30 segundos
setInterval(() => {
    loadStats();
    loadMatches();
}, 30000);
