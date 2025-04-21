import pkg from 'pg';
const { Pool } = pkg;
import os from 'os';

// Obter a URL do banco de dados do ambiente
const dbUrl = process.env.DATABASE_URL;

// Configurar a conexão com o banco de dados
const pool = new Pool({
  connectionString: dbUrl,
  ssl: {
    rejectUnauthorized: false
  }
});

// Função para inicializar o banco de dados com as tabelas necessárias
export async function initializeDatabase() {
  try {
    // Criar tabela de usuários se não existir
    await pool.query(`
      CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        uid TEXT UNIQUE NOT NULL,
        nome TEXT,
        email TEXT UNIQUE NOT NULL,
        provedor TEXT,
        foto_url TEXT,
        ultimo_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    
    console.log('Banco de dados inicializado com sucesso');
    return true;
  } catch (error) {
    console.error('Erro ao inicializar o banco de dados:', error);
    return false;
  }
}

export default pool;