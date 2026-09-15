// FigTreeKit Studio — 前端逻辑（纯 vanilla JS，无构建步骤）
// 薄前端原则：前端零业务逻辑，所有生成/渲染都发生在后端。
// 支持中英文界面切换（localStorage 持久化，首次按浏览器语言自动选择）。

(function () {
  'use strict';

  // ----------------------------------------------------------------------- //
  // i18n 词典（zh = 简体中文，en = English）
  // ----------------------------------------------------------------------- //
  const I18N = {
    zh: {
      tagline: '可视化调参 · 实时预览 · 可复现脚本导出',
      healthBtn: '环境检测', healthBtnTitle: '检查运行环境',
      secTree: '📂 树输入',
      treeText: 'Newick / Nexus 文本',
      treeTextPh: '粘贴 Newick 或 Nexus 树文本…',
      treeHint: '直接粘贴含 GTDB 分类标签的树可驱动自动配色/折叠。',
      treeFile: '或上传文件',
      secLayout: '🔀 布局', layout: '布局类型',
      layoutRect: 'rectilinear（矩形树）',
      layoutPolar: 'polar（极坐标）',
      layoutRadial: 'radial（放射状）',
      tipLabels: '末端标签', optShow: '显示 show', optHide: '隐藏 hide',
      alignTips: '径向对齐标签',
      secAppearance: '🎨 外观',
      bgColor: '背景色', branchWidth: '分支线宽',
      fgColor: '前景色', labelColor: '标签色',
      fontName: '字体名', fontNamePh: '如 Arial',
      fontSize: '字号 (pt)', fontStyle: '字体样式',
      curvature: '曲率 (矩形树)', curvaturePh: '-1=默认',
      collapseStyle: '折叠样式',
      comingSoon: '(TSV/CSV，规划中)',
      posBottom: 'bottom（下）', posTop: 'top（上）',
      posLeft: 'left（左）', posRight: 'right（右）',
      langBtnTitle: '切换语言 / Switch language',
      close: '关闭',
      renderTimeout: '渲染超时，请重试',
      inFlightMsg: '已有渲染任务在进行中…',
      secTaxonomy: '🧬 分类学',
      autoColorRank: '自动配色级别', optNone: '（无）',
      rankDomain: 'domain（域）', rankPhylum: 'phylum（门）',
      rankClass: 'class（纲）', rankOrder: 'order（目）',
      rankFamily: 'family（科）', rankGenus: 'genus（属）',
      rankSpecies: 'species（种）',
      collapseRank: '折叠级别',
      taxonomyFile: '分类映射文件',
      secScale: '📏 刻度与标签',
      scaleAxis: '刻度轴', scaleBar: '比例尺',
      optOff: '关', optShowShort: '显示', optHideShort: '隐藏',
      nodeLabels: '节点标签', nodeAttr: '节点属性', nodeAttrPh: '如 height',
      branchLabels: '分支标签', branchAttr: '分支属性', branchAttrPh: '如 length',
      secPolar: '🧭 极坐标参数',
      angularRange: '角度范围 (°)', rootAngle: '根角度 (°)', zeroDefault: '0=默认',
      secLegend: '📊 图例', legend: '图例', legendPos: '位置',
      secOutput: '🖼️ 输出', format: '格式', width: '图宽 (px)', height: '图高 (px)',
      generateBtn: '⚡ 生成预览 + 导出脚本',
      previewTitle: '📋 实时预览', rendering: '渲染中…',
      previewPlaceholder: '点击「生成预览」按钮开始',
      cliTitle: '① 等效 CLI 命令', jsonTitle: '② JSON 配置',
      copy: '复制', copied: '已复制',
      healthTitle: '环境检测', checking: '检测中…',
      healthFigtreekit: 'figtreekit 包', healthJar: 'JAR 文件', healthJava: 'Java',
      healthFail: '检测失败: ', healthNetFail: '请求失败: ',
      pdfDone: 'PDF 已生成，', pdfLink: '点击下载 PDF',
      genFail: '生成失败', requestErr: '请求错误',
      netFail: '网络请求失败: ', unknownErr: '未知错误',
      langBtn: 'EN',
      err: {
        no_tree: '请提供树文本或树文件',
        tree_file_read: '无法读取树文件',
        figtreekit_timeout: 'figtreekit 执行超时（树可能过大）',
        figtreekit_failed: 'figtreekit 生成失败',
        render_bad_format: '不支持的输出格式',
        jar_missing: '未找到 figtree_patched.jar，请运行 `python -m figtreekit --setup-figtree` 获取',
        java_missing: '未找到 Java，请安装 Java 8+ (JRE/JDK)',
        render_timeout: 'JAR 渲染超时',
        render_failed: 'JAR 渲染失败',
        internal_error: '内部错误',
        unknown: '未知错误',
      },
      // 这些错误码的原始 error 含技术细节（stderr 尾部等），需附加显示
      errDetailKeys: ['tree_file_read', 'figtreekit_failed', 'render_failed',
                      'render_bad_format', 'render_timeout', 'internal_error', 'figtreekit_timeout'],
    },
    en: {
      tagline: 'Visual tuning · Live preview · Reproducible exports',
      healthBtn: 'Environment', healthBtnTitle: 'Check runtime environment',
      secTree: '📂 Tree Input',
      treeText: 'Newick / Nexus text',
      treeTextPh: 'Paste Newick or Nexus tree text…',
      treeHint: 'Paste a tree with GTDB taxonomy labels to drive auto-coloring/collapse.',
      treeFile: 'Or upload a file',
      secLayout: '🔀 Layout', layout: 'Layout type',
      layoutRect: 'rectilinear (rectangular)',
      layoutPolar: 'polar (circular)',
      layoutRadial: 'radial (fan)',
      tipLabels: 'Tip labels', optShow: 'Show', optHide: 'Hide',
      alignTips: 'Align tip labels radially',
      secAppearance: '🎨 Appearance',
      bgColor: 'Background', branchWidth: 'Branch width',
      fgColor: 'Foreground', labelColor: 'Label color',
      fontName: 'Font name', fontNamePh: 'e.g. Arial',
      fontSize: 'Font size (pt)', fontStyle: 'Font style',
      curvature: 'Curvature (rectilinear)', curvaturePh: '-1=default',
      collapseStyle: 'Collapse style',
      comingSoon: '(TSV/CSV, planned)',
      posBottom: 'bottom', posTop: 'top',
      posLeft: 'left', posRight: 'right',
      langBtnTitle: 'Switch language / 切换语言',
      close: 'Close',
      renderTimeout: 'Render timed out, please retry',
      inFlightMsg: 'A render is already in progress…',
      secTaxonomy: '🧬 Taxonomy',
      autoColorRank: 'Auto-color rank', optNone: '(none)',
      rankDomain: 'domain', rankPhylum: 'phylum',
      rankClass: 'class', rankOrder: 'order',
      rankFamily: 'family', rankGenus: 'genus',
      rankSpecies: 'species',
      collapseRank: 'Collapse rank',
      taxonomyFile: 'Taxonomy mapping file',
      secScale: '📏 Scale & Labels',
      scaleAxis: 'Scale axis', scaleBar: 'Scale bar',
      optOff: 'Off', optShowShort: 'Show', optHideShort: 'Hide',
      nodeLabels: 'Node labels', nodeAttr: 'Node attribute', nodeAttrPh: 'e.g. height',
      branchLabels: 'Branch labels', branchAttr: 'Branch attribute', branchAttrPh: 'e.g. length',
      secPolar: '🧭 Polar options',
      angularRange: 'Angular range (°)', rootAngle: 'Root angle (°)', zeroDefault: '0=default',
      secLegend: '📊 Legend', legend: 'Legend', legendPos: 'Position',
      secOutput: '🖼️ Output', format: 'Format', width: 'Width (px)', height: 'Height (px)',
      generateBtn: '⚡ Generate Preview + Export Script',
      previewTitle: '📋 Live Preview', rendering: 'Rendering…',
      previewPlaceholder: 'Click "Generate Preview" to start',
      cliTitle: '① Equivalent CLI command', jsonTitle: '② JSON config',
      copy: 'Copy', copied: 'Copied',
      healthTitle: 'Environment Check', checking: 'Checking…',
      healthFigtreekit: 'figtreekit package', healthJar: 'JAR file', healthJava: 'Java',
      healthFail: 'Check failed: ', healthNetFail: 'Request failed: ',
      pdfDone: 'PDF generated, ', pdfLink: 'Click to download PDF',
      genFail: 'Generation failed', requestErr: 'Request error',
      netFail: 'Network request failed: ', unknownErr: 'Unknown error',
      langBtn: '中文',
      err: {
        no_tree: 'Please provide tree text or a tree file',
        tree_file_read: 'Failed to read the tree file',
        figtreekit_timeout: 'figtreekit timed out (tree may be too large)',
        figtreekit_failed: 'figtreekit generation failed',
        render_bad_format: 'Unsupported output format',
        jar_missing: 'figtree_patched.jar not found. Run `python -m figtreekit --setup-figtree` to fetch it',
        java_missing: 'Java not found. Please install Java 8+ (JRE/JDK)',
        render_timeout: 'JAR render timed out',
        render_failed: 'JAR render failed',
        internal_error: 'Internal error',
        unknown: 'Unknown error',
      },
      errDetailKeys: ['tree_file_read', 'figtreekit_failed', 'render_failed',
                      'render_bad_format', 'render_timeout', 'internal_error', 'figtreekit_timeout'],
    },
  };

  const LANG_KEY = 'ftks_lang';

  function currentLang() {
    let lang = null;
    try { lang = localStorage.getItem(LANG_KEY); } catch (e) { /* ignore */ }
    if (lang !== 'zh' && lang !== 'en') {
      lang = (navigator.language || '').toLowerCase().startsWith('zh') ? 'zh' : 'en';
    }
    return lang;
  }

  function t(key) {
    const lang = currentLang();
    const dict = I18N[lang] || I18N.zh;
    return dict[key] !== undefined ? dict[key] : (I18N.zh[key] !== undefined ? I18N.zh[key] : key);
  }

  function applyLang() {
    const lang = currentLang();
    const dict = I18N[lang] || I18N.zh;
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';

    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      const key = el.getAttribute('data-i18n');
      if (dict[key] !== undefined) el.textContent = dict[key];
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(function (el) {
      const key = el.getAttribute('data-i18n-ph');
      if (dict[key] !== undefined) el.setAttribute('placeholder', dict[key]);
    });
    document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      const key = el.getAttribute('data-i18n-title');
      if (dict[key] !== undefined) el.setAttribute('title', dict[key]);
    });
    document.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
      const key = el.getAttribute('data-i18n-aria');
      if (dict[key] !== undefined) el.setAttribute('aria-label', dict[key]);
    });
    const langBtn = document.getElementById('lang-btn');
    if (langBtn) langBtn.textContent = dict.langBtn;
    // 首屏语言应用完成，移除隐藏门控
    document.body.classList.remove('i18n-pending');
  }

  // ----------------------------------------------------------------------- //
  // DOM 快捷引用
  // ----------------------------------------------------------------------- //
  const $ = (id) => document.getElementById(id);

  // ----------------------------------------------------------------------- //
  // 安全数值读取（空值/非数字一律回退）
  // ----------------------------------------------------------------------- //
  function numOr(id, fallback) {
    const v = parseFloat($(id).value);
    return Number.isFinite(v) ? v : fallback;
  }

  // ----------------------------------------------------------------------- //
  // 收集表单参数
  // ----------------------------------------------------------------------- //
  function collectParams() {
    return {
      tree_text: $('tree_text').value,
      tree_file: $('tree_file').files[0] ? $('tree_file').files[0].name : '',
      layout: $('layout').value,
      tip_labels: $('tip_labels').value,
      align_tip_labels: $('align_tip_labels').checked,
      bg_color: $('bg_color').value,
      branch_width: numOr('branch_width', 0),
      foreground_color: $('foreground_color').value,
      font_name: $('font_name').value,
      font_size: Math.trunc(numOr('font_size', 0)),
      font_style: $('font_style').value,
      label_color: $('label_color').value,
      // curvature 不能用 || 党底，因为 0 是合法值（直线分支）
      curvature: Math.trunc(numOr('curvature', -1)),
      auto_color_rank: $('auto_color_rank').value,
      collapse_rank: $('collapse_rank').value,
      collapse_style: $('collapse_style').value,
      taxonomy_mapping_file: '',
      scale_axis: $('scale_axis').value,
      scale_bar: $('scale_bar').value,
      node_labels: $('node_labels').value,
      node_display_attribute: $('node_display_attribute').value,
      branch_labels: $('branch_labels').value,
      branch_display_attribute: $('branch_display_attribute').value,
      angular_range: Math.trunc(numOr('angular_range', 0)),
      root_angle: Math.trunc(numOr('root_angle', 0)),
      legend: $('legend').value,
      legend_position: $('legend_position').value,
      render_format: $('render_format').value,
      width: Math.trunc(numOr('width', 1600)),
      height: Math.trunc(numOr('height', 1000)),
    };
  }

  // ----------------------------------------------------------------------- //
  // 错误信息本地化（error_key → 当前语言；技术细节附加显示）
  // ----------------------------------------------------------------------- //
  function localizeError(d) {
    const key = d && d.error_key;
    const dict = I18N[currentLang()] || I18N.zh;
    if (key && dict.err[key]) {
      let msg = dict.err[key];
      if (dict.errDetailKeys.indexOf(key) !== -1 && d.error_detail) {
        msg += '\n' + d.error_detail;
      }
      return msg;
    }
    return (d && d.error) || dict.unknownErr;
  }

  // ----------------------------------------------------------------------- //
  // 生成预览
  // ----------------------------------------------------------------------- //
  let inFlight = false;  // 模块级在途保护，防止并发提交

  async function generate() {
    if (inFlight) return;  // 在途保护
    inFlight = true;

    const btn = $('generate-btn');
    const loading = $('loading-indicator');
    const preview = $('preview');
    const errEl = $('error-msg');

    btn.disabled = true;
    loading.classList.remove('hidden');
    errEl.textContent = '';
    preview.setAttribute('aria-busy', 'true');
    preview.innerHTML = '<span class="placeholder"></span>';
    preview.querySelector('.placeholder').textContent = t('rendering');

    // fetch 超时与取消
    const ctrl = new AbortController();
    const timer = setTimeout(function () { ctrl.abort(); }, 200000);

    try {
      const params = collectParams();
      const r = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
        signal: ctrl.signal,
      });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const d = await r.json();

      if (d.ok) {
        // 图片预览
        const fmt = params.render_format || 'PNG';
        if (fmt === 'PDF') {
          // PDF 不能内嵌为 img，提供下载链接
          preview.innerHTML = '<span class="placeholder"></span>';
          const link = document.createElement('a');
          link.href = d.image;
          link.download = 'output.pdf';
          link.style.color = 'var(--accent)';
          link.style.fontWeight = '600';
          preview.querySelector('.placeholder').textContent = t('pdfDone');
          preview.appendChild(link);
          link.textContent = t('pdfLink');
        } else {
          // 用 DOM 构建而非 innerHTML 拼接，保持 XSS 卫生
          preview.innerHTML = '';
          const img = new Image();
          img.src = d.image;
          img.alt = '';
          preview.appendChild(img);
        }
        // CLI 命令
        $('cli-output').textContent = d.command || '—';
        // JSON 配置
        $('json-output').textContent = d.config_json || '—';
      } else {
        preview.innerHTML = '<span class="placeholder"></span>';
        preview.querySelector('.placeholder').textContent = t('genFail');
        errEl.textContent = localizeError(d);
      }
    } catch (e) {
      preview.innerHTML = '<span class="placeholder"></span>';
      if (e.name === 'AbortError') {
        preview.querySelector('.placeholder').textContent = t('renderTimeout');
        errEl.textContent = t('renderTimeout');
      } else {
        preview.querySelector('.placeholder').textContent = t('requestErr');
        errEl.textContent = t('netFail') + e;
      }
    } finally {
      clearTimeout(timer);
      inFlight = false;
      btn.disabled = false;
      loading.classList.add('hidden');
      preview.setAttribute('aria-busy', 'false');
    }
  }

  // ----------------------------------------------------------------------- //
  // 复制按钮
  // ----------------------------------------------------------------------- //
  function flashCopied(btn) {
    btn.classList.add('copied');
    btn.textContent = t('copied');
    setTimeout(function () {
      btn.classList.remove('copied');
      btn.textContent = t('copy');
    }, 1500);
  }

  function setupCopyButtons() {
    document.querySelectorAll('.btn-copy').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const targetId = btn.getAttribute('data-target');
        const text = $(targetId).textContent;
        if (!text || text === '—') return;

        const fallback = function () {
          const ta = document.createElement('textarea');
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          flashCopied(btn);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(function () {
            flashCopied(btn);
          }, fallback);
        } else {
          fallback();
        }
      });
    });
  }

  // ----------------------------------------------------------------------- //
  // 颜色选择器联动
  // ----------------------------------------------------------------------- //
  function setupColorPickers() {
    function link(pickerId, textId) {
      const picker = $(pickerId);
      const text = $(textId);
      if (!picker || !text) return;

      picker.addEventListener('input', function () {
        text.value = picker.value.toUpperCase();
      });
      text.addEventListener('input', function () {
        const v = text.value.trim();
        if (/^#[0-9a-fA-F]{6}$/.test(v)) {
          picker.value = v.toLowerCase();
        }
      });
    }
    link('bg_color_picker', 'bg_color');
    link('fg_color_picker', 'foreground_color');
    link('label_color_picker', 'label_color');
  }

  // ----------------------------------------------------------------------- //
  // 文件上传：读取到 textarea
  // ----------------------------------------------------------------------- //
  function setupFileUpload() {
    $('tree_file').addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function (ev) {
        $('tree_text').value = ev.target.result;
      };
      reader.readAsText(file);
    });
  }

  // ----------------------------------------------------------------------- //
  // 健康检查
  // ----------------------------------------------------------------------- //
  async function healthCheck() {
    const body = $('health-body');
    body.textContent = t('checking');

    try {
      const r = await fetch('/api/health');
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const d = await r.json();
      if (d.ok) {
        const jarOk = d.jar_ok !== undefined ? d.jar_ok : (d.jar && d.jar !== '(not found)');
        const javaOk = d.java_ok !== undefined ? d.java_ok : !!(d.java && d.java.indexOf('not') === -1);
        const ftkOk = !!d.figtreekit && d.figtreekit !== '(not found)';

        // 用 DOM 构建而非 innerHTML 拼接，保持 XSS 卫生
        function healthRow(labelKey, value, ok) {
          const row = document.createElement('div');
          const mark = document.createElement('span');
          mark.className = ok ? 'ok' : 'fail';
          mark.textContent = ok ? '✓' : '✗';
          row.appendChild(mark);
          row.appendChild(document.createTextNode(' ' + t(labelKey) + ': ' + (value || 'N/A')));
          return row;
        }

        body.textContent = '';
        body.appendChild(healthRow('healthFigtreekit', d.figtreekit, ftkOk));
        body.appendChild(healthRow('healthJar', d.jar, jarOk));
        body.appendChild(healthRow('healthJava', d.java, javaOk));
      } else {
        body.textContent = '';
        const span = document.createElement('span');
        span.className = 'fail';
        span.textContent = t('healthFail') + (d.error || '');
        body.appendChild(span);
      }
    } catch (e) {
      body.textContent = '';
      const span = document.createElement('span');
      span.className = 'fail';
      span.textContent = t('healthNetFail') + e;
      body.appendChild(span);
    }
  }

  function setupHealthModal() {
    const modal = $('health-modal');
    let lastFocus = null;

    function openModal() {
      lastFocus = document.activeElement;
      modal.classList.remove('hidden');
      $('health-close').focus();  // 焦点移入对话框
      healthCheck();
    }
    function closeModal() {
      modal.classList.add('hidden');
      if (lastFocus) lastFocus.focus();  // 焦点归还原处
    }

    $('health-btn').addEventListener('click', openModal);
    $('health-close').addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) {
      if (e.target === modal) closeModal();
    });
    // Esc 关闭弹窗
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modal.classList.contains('hidden')) closeModal();
    });
  }

  // ----------------------------------------------------------------------- //
  // 语言切换
  // ----------------------------------------------------------------------- //
  function setupLangToggle() {
    $('lang-btn').addEventListener('click', function () {
      const next = currentLang() === 'zh' ? 'en' : 'zh';
      try { localStorage.setItem(LANG_KEY, next); } catch (e) { /* ignore */ }
      applyLang();
    });
  }

  // ----------------------------------------------------------------------- //
  // 键盘快捷键：Cmd/Ctrl+Enter 生成
  // ----------------------------------------------------------------------- //
  function setupShortcuts() {
    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        generate();
      }
    });
  }

  // ----------------------------------------------------------------------- //
  // 初始化
  // ----------------------------------------------------------------------- //
  document.addEventListener('DOMContentLoaded', function () {
    applyLang();
    $('generate-btn').addEventListener('click', generate);
    setupCopyButtons();
    setupColorPickers();
    setupFileUpload();
    setupHealthModal();
    setupLangToggle();
    setupShortcuts();
  });
})();
