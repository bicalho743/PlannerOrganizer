"""
Script para injetar códigos de analytics e meta tags de SEO diretamente no HTML da página
"""
import streamlit as st
import streamlit.components.v1 as components

def inject_analytics_tags():
    """
    Injeta as tags do Google Analytics, Google Tag Manager e Facebook Pixel na página
    """
    
    # Código combinado de GA4 + GTM + Facebook Pixel
    analytics_code = """
    <!-- Google Analytics 4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-E9KP3F40VT"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-E9KP3F40VT');
    </script>
    
    <!-- Google Tag Manager -->
    <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','GTM-NM45ZQCD');</script>
    
    <!-- Facebook Pixel -->
    <script>
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', '654529850558184');
    fbq('track', 'PageView');
    </script>
    
    <!-- Brevo Tracking -->
    <script src="https://cdn.brevo.com/js/sdk-loader.js" async></script>
    <script>
        // Version: 2.0
        window.Brevo = window.Brevo || [];
        Brevo.push([
            "init",
            {
            client_key: "awheq5vyxe050fhs5oxcejmb",
            // Optional: Add other initialization options, see documentation
            }
        ]);
    </script>
    
    <!-- Noscript tags -->
    <noscript>
        <iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NM45ZQCD"
        height="0" width="0" style="display:none;visibility:hidden"></iframe>
        <img height="1" width="1" style="display:none"
        src="https://www.facebook.com/tr?id=654529850558184&ev=PageView&noscript=1" />
    </noscript>
    
    <script>
    // Verificação de carregamento das tags
    setTimeout(function() {
        if (typeof gtag !== 'undefined') {
            console.log('Google Analytics carregado com sucesso');
        }
        if (typeof dataLayer !== 'undefined') {
            console.log('DataLayer inicializado com sucesso');
        }
        if (typeof fbq !== 'undefined') {
            console.log('Facebook Pixel carregado com sucesso');
        }
        if (typeof Brevo !== 'undefined') {
            console.log('Brevo tracking carregado com sucesso');
        }
    }, 2000);
    </script>
    """
    
    # Injeta o código no head usando components.html
    components.html(analytics_code, height=0)

def inject_seo_meta_tags(page_title="Planner Organizer | Sistema para Personal Organizers", 
                        description="Organize clientes, propostas e finanças em um só lugar. Sistema completo para Personal Organizers. Teste grátis por 7 dias!",
                        keywords="personal organizer, sistema organizador, gestão clientes, propostas, organização profissional"):
    """
    Injeta meta tags de SEO otimizados na página
    
    Args:
        page_title (str): Título da página para SEO
        description (str): Meta description para SEO
        keywords (str): Palavras-chave para SEO
    """
    
    seo_meta_tags = f"""
    <script>
    // Atualizar título da página
    document.title = "{page_title}";
    
    // Remover meta tags existentes se houver
    var existingMeta = document.querySelectorAll('meta[name="description"], meta[name="keywords"], meta[property^="og:"], meta[name="twitter:"]');
    existingMeta.forEach(function(meta) {{
        meta.remove();
    }});
    
    // Criar e adicionar novos meta tags
    var metaTags = [
        // Meta básicos
        {{ name: 'description', content: '{description}' }},
        {{ name: 'keywords', content: '{keywords}' }},
        {{ name: 'author', content: 'Planner Organizer' }},
        {{ name: 'robots', content: 'index, follow' }},
        {{ name: 'viewport', content: 'width=device-width, initial-scale=1.0' }},
        
        // Open Graph para redes sociais
        {{ property: 'og:title', content: '{page_title}' }},
        {{ property: 'og:description', content: '{description}' }},
        {{ property: 'og:type', content: 'website' }},
        {{ property: 'og:url', content: window.location.href }},
        {{ property: 'og:site_name', content: 'Planner Organizer' }},
        {{ property: 'og:locale', content: 'pt_BR' }},
        
        // Twitter Cards
        {{ name: 'twitter:card', content: 'summary_large_image' }},
        {{ name: 'twitter:title', content: '{page_title}' }},
        {{ name: 'twitter:description', content: '{description}' }},
        
        // Meta tags específicos para Brasil
        {{ name: 'geo.region', content: 'BR' }},
        {{ name: 'geo.country', content: 'Brazil' }},
        {{ name: 'language', content: 'Portuguese' }}
    ];
    
    metaTags.forEach(function(tagInfo) {{
        var meta = document.createElement('meta');
        if (tagInfo.name) {{
            meta.name = tagInfo.name;
        }} else if (tagInfo.property) {{
            meta.setAttribute('property', tagInfo.property);
        }}
        meta.content = tagInfo.content;
        document.head.appendChild(meta);
    }});
    
    console.log('SEO Meta tags injetados com sucesso');
    </script>
    """
    
    # Injeta os meta tags no head
    components.html(seo_meta_tags, height=0)

def inject_seo_headings():
    """
    Injeta headings estruturados para melhorar SEO
    """
    seo_headings = """
    <div style="display: none; position: absolute; left: -9999px;">
        <h1>Planner Organizer: sistema de gestão para Personal Organizer</h1>
        <h2>Organização profissional com tecnologia</h2>
        <h2>Um sistema de propostas feito para você</h2>
        <h2>Gestão completa para Personal Organizer</h2>
        <h2>Por que escolher o Planner Organizer?</h2>
        <h2>Planner Organizer: tecnologia a favor da sua organização</h2>
        <p>Se você é uma <strong>personal organizer</strong> e busca mais eficiência, praticidade e organização no seu dia a dia, o <strong>Planner Organizer</strong> foi feito para você.</p>
        <p>A profissão de personal organizer exige controle, planejamento e visão estratégica. Pensando nisso, o Planner Organizer oferece uma plataforma completa e intuitiva.</p>
        <p>Chega de planilhas confusas ou anotações soltas. Com o <strong>sistema de propostas</strong> do Planner Organizer, você cria, envia e acompanha propostas com agilidade.</p>
    </div>
    """
    
    st.markdown(seo_headings, unsafe_allow_html=True)

def inject_structured_data():
    """
    Injeta dados estruturados JSON-LD para melhorar SEO
    """
    structured_data = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Planner Organizer",
        "description": "Sistema completo de gestão para Personal Organizers. Organize clientes, propostas e finanças em um só lugar.",
        "url": "https://plannerorganizer.com.br",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "BRL",
            "description": "Teste grátis por 7 dias"
        },
        "creator": {
            "@type": "Organization",
            "@id": "https://plannerorganizer.com.br",
            "name": "Planner Organizer",
            "description": "Especialistas em soluções para Personal Organizers"
        },
        "featureList": [
            "Gestão de clientes",
            "Sistema de propostas",
            "Controle financeiro",
            "Relatórios inteligentes",
            "Acesso mobile"
        ],
        "audience": {
            "@type": "Audience",
            "audienceType": "Personal Organizers"
        },
        "inLanguage": "pt-BR",
        "geo": {
            "@type": "Place",
            "addressCountry": "BR"
        }
    }
    </script>
    """
    
    components.html(structured_data, height=0)

def inject_breadcrumbs(page_name="Home"):
    """
    Injeta breadcrumbs estruturados para melhorar navegação e SEO
    """
    breadcrumb_schema = f"""
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {{
                "@type": "ListItem",
                "position": 1,
                "name": "Planner Organizer",
                "item": "https://plannerorganizer.com.br"
            }},
            {{
                "@type": "ListItem",
                "position": 2,
                "name": "{page_name}",
                "item": "https://plannerorganizer.com.br/{page_name.lower()}"
            }}
        ]
    }}
    </script>
    """
    
    components.html(breadcrumb_schema, height=0)

def inject_organization_schema():
    """
    Injeta schema de organização para melhorar SEO local
    """
    organization_schema = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Planner Organizer",
        "url": "https://plannerorganizer.com.br",
        "logo": "https://plannerorganizer.com.br/app-icon.svg",
        "description": "Sistema completo de gestão para Personal Organizers no Brasil",
        "areaServed": {
            "@type": "Country",
            "name": "Brasil"
        },
        "serviceType": "Software de Gestão",
        "audience": {
            "@type": "Audience",
            "audienceType": "Personal Organizers"
        },
        "offers": {
            "@type": "Offer",
            "name": "Teste Grátis",
            "description": "7 dias de teste gratuito",
            "price": "0",
            "priceCurrency": "BRL"
        }
    }
    </script>
    """
    
    components.html(organization_schema, height=0)

def inject_optimized_images():
    """
    Injeta CSS para otimizar imagens com alt text para SEO
    """
    image_optimization = """
    <style>
    /* Otimização de imagens para SEO */
    img {
        max-width: 100%;
        height: auto;
        loading: lazy;
    }
    
    /* Imagens específicas do sistema */
    .logo-planner {
        alt: "Logo Planner Organizer - Sistema de gestão para personal organizers";
    }
    
    .dashboard-image {
        alt: "Dashboard financeiro para personal organizer no Planner Organizer";
    }
    
    .propostas-image {
        alt: "Sistema de propostas profissionais para personal organizers";
    }
    
    .clientes-image {
        alt: "Gestão de clientes para personal organizer - Planner Organizer";
    }
    
    .relatorios-image {
        alt: "Relatórios inteligentes para personal organizer no Planner Organizer";
    }
    </style>
    
    <script>
    // Adiciona alt text otimizado automaticamente para imagens sem descrição
    document.addEventListener('DOMContentLoaded', function() {
        const images = document.querySelectorAll('img:not([alt])');
        images.forEach(function(img) {
            if (img.src.includes('dashboard')) {
                img.alt = 'Dashboard financeiro para personal organizer no Planner Organizer';
            } else if (img.src.includes('proposta')) {
                img.alt = 'Sistema de propostas profissionais para personal organizers';
            } else if (img.src.includes('cliente')) {
                img.alt = 'Gestão de clientes para personal organizer - Planner Organizer';
            } else if (img.src.includes('relatorio')) {
                img.alt = 'Relatórios inteligentes para personal organizer no Planner Organizer';
            } else {
                img.alt = 'Planner Organizer - Sistema completo para personal organizers';
            }
        });
    });
    </script>
    """
    
    components.html(image_optimization, height=0)

def inject_performance_meta_tags():
    """
    Injeta meta tags para melhorar performance e SEO técnico
    """
    performance_tags = """
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
    <meta name="googlebot" content="index, follow">
    <meta name="bingbot" content="index, follow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#667eea">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Planner Organizer">
    
    <!-- Preload recursos críticos -->
    <link rel="preload" href="/app-icon.svg" as="image" type="image/svg+xml">
    <link rel="dns-prefetch" href="//www.google-analytics.com">
    <link rel="dns-prefetch" href="//connect.facebook.net">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="https://plannerorganizer.com.br/">
    
    <!-- Sitemap -->
    <link rel="sitemap" type="application/xml" href="/sitemap.xml">
    """
    
    components.html(performance_tags, height=0)

def inject_local_business_schema():
    """
    Injeta schema específico para negócio local brasileiro
    """
    local_business_schema = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": "https://plannerorganizer.com.br",
        "name": "Planner Organizer",
        "url": "https://plannerorganizer.com.br",
        "description": "Sistema de gestão completo para Personal Organizers no Brasil. Gerencie clientes, propostas e finanças em uma plataforma intuitiva.",
        "foundingDate": "2024",
        "areaServed": {
            "@type": "Country",
            "name": "Brasil",
            "sameAs": "https://pt.wikipedia.org/wiki/Brasil"
        },
        "serviceType": "Software de Gestão Empresarial",
        "priceRange": "Teste grátis por 7 dias",
        "paymentAccepted": "Cartão de Crédito, PIX, Boleto",
        "currenciesAccepted": "BRL",
        "openingHours": "Mo-Su 00:00-23:59",
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Serviços para Personal Organizers",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": "Sistema de Gestão de Clientes",
                        "description": "Organize e gerencie todos os seus clientes em um só lugar"
                    }
                },
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": "Gerador de Propostas",
                        "description": "Crie propostas profissionais personalizadas rapidamente"
                    }
                },
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": "Controle Financeiro",
                        "description": "Acompanhe receitas, despesas e lucros do seu negócio"
                    }
                }
            ]
        }
    }
    </script>
    """
    
    components.html(local_business_schema, height=0)

def inject_performance_optimizations():
    """
    Injeta otimizações de performance para melhorar velocidade da página
    """
    performance_optimizations = """
    <style>
    /* Otimizações de performance CSS */
    * {
        box-sizing: border-box;
    }
    
    /* Lazy loading para imagens */
    img {
        loading: lazy;
        max-width: 100%;
        height: auto;
    }
    
    /* Otimização de fontes */
    @font-face {
        font-display: swap;
    }
    
    /* Redução de reflows */
    .main > div {
        contain: layout style paint;
    }
    
    /* Aceleração de hardware para animações */
    .header-gradient {
        transform: translateZ(0);
        will-change: transform;
    }
    
    /* Otimização de scroll */
    .main {
        scroll-behavior: smooth;
    }
    </style>
    
    <script>
    // Lazy loading para elementos não críticos
    if ('IntersectionObserver' in window) {
        const lazyElements = document.querySelectorAll('[data-lazy]');
        const lazyObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    element.src = element.dataset.src;
                    element.removeAttribute('data-lazy');
                    lazyObserver.unobserve(element);
                }
            });
        });
        
        lazyElements.forEach((element) => {
            lazyObserver.observe(element);
        });
    }
    
    // Preload recursos críticos
    const criticalResources = [
        '/app-icon.svg',
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap'
    ];
    
    criticalResources.forEach(resource => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = resource;
        link.as = resource.includes('.css') ? 'style' : 'image';
        document.head.appendChild(link);
    });
    
    // Minificação de scripts inline
    document.addEventListener('DOMContentLoaded', function() {
        // Remove comentários desnecessários do DOM
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_COMMENT,
            null,
            false
        );
        
        const comments = [];
        let node;
        while (node = walker.nextNode()) {
            comments.push(node);
        }
        
        comments.forEach(comment => {
            if (!comment.nodeValue.includes('SEO') && !comment.nodeValue.includes('Analytics')) {
                comment.parentNode.removeChild(comment);
            }
        });
    });
    
    // Compressão de dados do localStorage
    if (typeof(Storage) !== "undefined") {
        const originalSetItem = localStorage.setItem;
        localStorage.setItem = function(key, value) {
            try {
                const compressed = LZString ? LZString.compress(value) : value;
                originalSetItem.call(this, key, compressed);
            } catch (e) {
                originalSetItem.call(this, key, value);
            }
        };
    }
    </script>
    
    <!-- Preconnect para recursos externos -->
    <link rel="preconnect" href="https://www.google-analytics.com">
    <link rel="preconnect" href="https://connect.facebook.net">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    
    <!-- DNS prefetch para domínios externos -->
    <link rel="dns-prefetch" href="//api.brevo.com">
    <link rel="dns-prefetch" href="//firebaseio.com">
    """
    
    components.html(performance_optimizations, height=0)

def inject_compression_headers():
    """
    Injeta headers para compressão e cache
    """
    compression_headers = """
    <meta http-equiv="Content-Encoding" content="gzip">
    <meta http-equiv="Cache-Control" content="public, max-age=31536000">
    <meta http-equiv="Expires" content="31536000">
    
    <script>
    // Service Worker para cache e compressão
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/sw.js').then(function(registration) {
                console.log('SW registrado: ', registration.scope);
            }, function(err) {
                console.log('SW falhou: ', err);
            });
        });
    }
    
    // Compressão de imagens automática
    function compressImage(file, quality = 0.8) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.onload = () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                
                canvas.toBlob(resolve, 'image/webp', quality);
            };
            
            img.src = URL.createObjectURL(file);
        });
    }
    
    // Otimização de requests
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const [resource, config] = args;
        const optimizedConfig = {
            ...config,
            headers: {
                ...config?.headers,
                'Accept-Encoding': 'gzip, deflate, br'
            }
        };
        return originalFetch(resource, optimizedConfig);
    };
    </script>
    """
    
    components.html(compression_headers, height=0)

def track_page_view(page_name="Home"):
    """
    Rastreia uma visualização de página no Google Analytics e Facebook Pixel
    """
    tracking_script = """
    <script>
    setTimeout(function() {
        // Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_view', {
                page_title: '""" + page_name + """',
                page_location: window.location.href
            });
            console.log('GA4 Page view tracked: """ + page_name + """');
        }
        
        // Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', 'PageView');
            console.log('Facebook Pixel PageView tracked: """ + page_name + """');
        }
    }, 1000);
    </script>
    """
    
    components.html(tracking_script, height=0)

def track_facebook_event(event_name, parameters=None):
    """
    Rastreia eventos específicos no Facebook Pixel
    
    Args:
        event_name (str): Nome do evento (ex: 'Lead', 'Purchase', 'AddToCart')
        parameters (dict): Parâmetros adicionais do evento
    """
    params_str = ""
    if parameters:
        import json
        params_str = f", {json.dumps(parameters)}"
    
    tracking_script = f"""
    <script>
    setTimeout(function() {{
        if (typeof fbq !== 'undefined') {{
            fbq('track', '{event_name}'{params_str});
            console.log('Facebook Pixel event tracked: {event_name}');
        }} else {{
            console.log('Facebook Pixel not available yet');
        }}
    }}, 500);
    </script>
    """
    
    components.html(tracking_script, height=0)