import express from 'express';
import pool from '../db.js';

const router = express.Router();

// Rota para salvar ou atualizar um usuário no banco de dados
router.post('/salvar-usuario', async (req, res) => {
  const { uid, nome, email, provedor, foto_url } = req.body;

  // Validar os dados obrigatórios
  if (!uid || !email) {
    return res.status(400).json({ 
      sucesso: false, 
      mensagem: 'UID e email são obrigatórios' 
    });
  }

  try {
    // Verificar se o usuário já existe
    const userCheck = await pool.query(
      'SELECT * FROM usuarios WHERE uid = $1 OR email = $2',
      [uid, email]
    );

    if (userCheck.rows.length > 0) {
      // Usuário já existe, atualizar os dados
      const result = await pool.query(
        `UPDATE usuarios 
         SET nome = $1, provedor = $2, foto_url = $3, ultimo_login = CURRENT_TIMESTAMP
         WHERE uid = $4
         RETURNING *`,
        [nome, provedor, foto_url, uid]
      );

      return res.status(200).json({
        sucesso: true,
        mensagem: 'Usuário atualizado com sucesso',
        usuario: result.rows[0]
      });
    } else {
      // Novo usuário, inserir no banco
      const result = await pool.query(
        `INSERT INTO usuarios (uid, nome, email, provedor, foto_url)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING *`,
        [uid, nome, email, provedor, foto_url]
      );

      return res.status(201).json({
        sucesso: true,
        mensagem: 'Usuário cadastrado com sucesso',
        usuario: result.rows[0]
      });
    }
  } catch (error) {
    console.error('Erro ao salvar usuário:', error);
    
    return res.status(500).json({
      sucesso: false,
      mensagem: 'Erro interno ao salvar usuário',
      erro: error.message
    });
  }
});

// Rota para obter um usuário pelo UID
router.get('/usuario/:uid', async (req, res) => {
  const { uid } = req.params;

  try {
    const result = await pool.query(
      'SELECT * FROM usuarios WHERE uid = $1',
      [uid]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        sucesso: false,
        mensagem: 'Usuário não encontrado'
      });
    }

    return res.status(200).json({
      sucesso: true,
      usuario: result.rows[0]
    });
  } catch (error) {
    console.error('Erro ao buscar usuário:', error);
    
    return res.status(500).json({
      sucesso: false,
      mensagem: 'Erro interno ao buscar usuário',
      erro: error.message
    });
  }
});

export default router;