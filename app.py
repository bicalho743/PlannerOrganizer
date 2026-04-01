<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Preview — Login Planner Organizer</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body {
  min-height:100vh;
  font-family:'DM Sans', sans-serif;
  background:
    radial-gradient(ellipse 60% 50% at 30% 20%, rgba(201,168,76,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 40% 60% at 70% 80%, rgba(26,48,96,0.4) 0%, transparent 60%),
    #0D1B35;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding:2rem 1rem;
}

/* Logo */
.logo { text-align:center; margin-bottom:2rem; }
.logo h1 {
  font-family:'Cormorant Garamond', serif;
  font-size:2rem; font-weight:600;
  color:#F5F0E8; letter-spacing:0.02em;
}
.logo p {
  font-size:0.72rem; color:rgba(245,240,232,0.38);
  text-transform:uppercase; letter-spacing:0.15em; margin-top:5px;
}

/* Card */
.card {
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(201,168,76,0.18);
  border-radius:20px; padding:2.5rem 2rem;
  width:100%; max-width:400px;
  backdrop-filter:blur(20px);
}
.card-title {
  font-family:'Cormorant Garamond', serif;
  font-size:1.5rem; font-weight:500;
  color:#F5F0E8; text-align:center; margin-bottom:0.25rem;
}
.card-sub {
  font-size:0.8rem; color:rgba(245,240,232,0.38);
  text-align:center; margin-bottom:1.75rem;
}

/* Form */
.form-group { margin-bottom:1rem; }
.form-group label {
  display:block; font-size:0.72rem; font-weight:500;
  text-transform:uppercase; letter-spacing:0.09em;
  color:rgba(245,240,232,0.55); margin-bottom:6px;
}
.form-group input {
  width:100%; background:rgba(255,255,255,0.06);
  border:1px solid rgba(201,168,76,0.22); border-radius:10px;
  color:#F5F0E8; padding:0.75rem 1rem;
  font-family:'DM Sans', sans-serif; font-size:0.875rem;
  outline:none; transition:border-color 0.2s, background 0.2s;
}
.form-group input::placeholder { color:rgba(245,240,232,0.22); }
.form-group input:focus {
  border-color:rgba(201,168,76,0.55);
  background:rgba(255,255,255,0.08);
  box-shadow:0 0 0 3px rgba(201,168,76,0.08);
}

/* Botão entrar */
.btn-primary {
  width:100%; padding:0.85rem;
  background:linear-gradient(135deg, #C9A84C, #9E7A10);
  color:#0D1B35; border:none; border-radius:10px;
  font-family:'DM Sans', sans-serif; font-size:0.875rem;
  font-weight:700; letter-spacing:0.06em;
  cursor:pointer; margin-top:0.5rem;
  transition:opacity 0.2s;
}
.btn-primary:hover { opacity:0.88; }

/* Botões secundários */
.btn-row { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px; }
.btn-secondary {
  padding:0.65rem; background:transparent;
  border:1px solid rgba(201,168,76,0.22); border-radius:10px;
  color:rgba(245,240,232,0.55); font-family:'DM Sans', sans-serif;
  font-size:0.78rem; cursor:pointer; transition:all 0.2s;
}
.btn-secondary:hover {
  border-color:rgba(201,168,76,0.5);
  color:#C9A84C; background:rgba(201,168,76,0.06);
}

/* Footer */
.footer {
  text-align:center; margin-top:1.5rem; font-size:0.75rem;
}
.footer a { color:rgba(245,240,232,0.3); text-decoration:none; transition:color 0.2s; }
.footer a:hover { color:rgba(245,240,232,0.65); }
.footer span { color:rgba(245,240,232,0.12); margin:0 0.4rem; }

/* Badge preview */
.preview-badge {
  position:fixed; top:16px; right:16px;
  background:rgba(201,168,76,0.15); border:1px solid rgba(201,168,76,0.3);
  color:#C9A84C; font-size:0.72rem; font-weight:500;
  padding:6px 14px; border-radius:20px;
  font-family:'DM Sans', sans-serif; letter-spacing:0.08em;
}
</style>
</head>
<body>

<div class="preview-badge">PREVIEW</div>

<div class="logo">
  <h1>Planner Organizer</h1>
  <p>Sistema para Personal Organizers</p>
</div>

<div class="card">
  <p class="card-title">Bem-vinda de volta ✦</p>
  <p class="card-sub">Acesse sua conta para continuar</p>

  <div class="form-group">
    <label>E-mail</label>
    <input type="email" placeholder="seu@email.com"/>
  </div>
  <div class="form-group">
    <label>Senha</label>
    <input type="password" placeholder="••••••••"/>
  </div>

  <button class="btn-primary">Entrar na minha conta</button>

  <div class="btn-row">
    <button class="btn-secondary">Esqueci a senha</button>
    <button class="btn-secondary">Criar conta grátis</button>
  </div>
</div>

<div class="footer">
  <a href="#">← Voltar ao site</a>
  <span>·</span>
  <a href="#">Termos de uso</a>
  <span>·</span>
  <a href="#">Privacidade</a>
</div>

</body>
</html>