import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { initializeDatabase } from './db.js';
import usuariosRouter from './routes/usuarios.js';

const app = express();
const PORT = process.env.PORT || 8000;

// Configurar middlewares
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Servir arquivos estáticos
app.use(express.static('public'));

// Configurar rotas
app.use('/api', usuariosRouter);

// Rota principal
app.get('/', (req, res) => {
  res.sendFile('login.html', { root: 'public' });
});

// Rota de teste de status
app.get('/status', (req, res) => {
  res.json({ status: 'online', timestamp: new Date() });
});

// Inicializar o banco de dados e iniciar o servidor
async function iniciarServidor() {
  try {
    // Inicializar o banco de dados
    await initializeDatabase();
    
    // Iniciar o servidor em 0.0.0.0 para estar acessível externamente
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`Servidor rodando em http://0.0.0.0:${PORT}`);
    });
  } catch (error) {
    console.error('Erro ao iniciar o servidor:', error);
    process.exit(1);
  }
}

iniciarServidor();