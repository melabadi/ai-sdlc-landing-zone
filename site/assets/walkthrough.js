(() => {
  "use strict";
  const copy = {
    en: {
      title: "AI SDLC · The walkthrough", skip: "Skip to the content",
      header: "GITHUB / AI ACROSS THE SDLC", fullscreen: "Full screen",
      exitFullscreen: "Exit full screen", repository: "Repository",
      eyebrow: "SEVEN PHASES. ONE CONNECTED LIFECYCLE.",
      principle: "Where AI fits. How we put it to work.",
      input: "Start with", output: "Pass forward", tools: "Technology spotlight",
      checks: "Verified by", decision: "Decided by", sources: "Technology references",
      sourceNote: "This deck describes our implementation pattern, not a live run. Product capabilities are documented below; the controls and handoffs are our choices.",
      speed: "Seconds / step", play: "Autoslide", pause: "Pause",
      guardrail: "Human approval is a boundary, not a shortcut.",
      keyboard: "← → Navigate · Home / End · Space Play / Pause",
      previous: "Previous step", next: "Next step", nextPhase: "Next phase", end: "End", nav: "SDLC phases",
      phase: "PHASE", step: "Step", inside: "In this phase", handoff: "Decision & handoff",
      roles: {app: "Interactive AI · desktop app", interactive: "Interactive AI", delegated: "Delegated AI", event: "Event-driven AI",
        guidance: "Reusable AI guidance", review: "AI review", check: "Deterministic automation · not AI",
        control: "Enforced permissions · not AI"},
      fullscreenError: "Full screen could not be changed. Use your browser's full-screen control.",
      unavailable: "Full screen is unavailable in this browser.",
      phases: [
        {
          name: "Plan", title: "Turn intent into clear requirements.",
          input: "Stakeholder notes + business policies",
          checks: "JSON Schema + source-citation validation", decision: "Product owner approves scope and resolves conflicts.",
          recipient: "Design", output: "Agreed requirements, acceptance criteria, and open questions.",
          steps: [
            ["app", "GitHub Copilot app · Plan mode", "The analyst opens a repository session and asks Copilot to compare workshop notes with business rules. The product owner resolves the conflicts and sets the scope.", "“Which requirements conflict? Cite both sources.”"],
            ["guidance", "Custom agents + Agent Skills", "The plan-github profile defines the role. The requirements-traceability skill supplies the procedure for citations and testable acceptance criteria.", "Role: .agent.md  /  Procedure: SKILL.md"],
            ["delegated", "GitHub Copilot cloud agent", "For asynchronous work, assign the planning Issue to the specialist. It drafts the requirements in a pull request for the product owner to review.", "Issue assignment → plan-github → pull request"]
          ]
        },
        {
          name: "Design", title: "Explore options against your standards.",
          input: "Requirements + architecture standards + existing code",
          checks: "ADR structure + OpenAPI compatibility", decision: "Architect accepts the trade-offs; policy owners resolve conflicts.",
          recipient: "Develop", output: "An accepted approach, API boundaries, and implementation tasks.",
          steps: [
            ["app", "GitHub Copilot app · Interactive mode", "The architect opens a repository session with the approved brief and compares two options against the current API. Copilot explains the trade-offs; the architect chooses the approach.", "“Which option preserves the OpenAPI contract, and why?”"],
            ["event", "GitHub Agentic Workflows", "For a second opinion, the architect posts /design-review. The workflow compares the proposal with repository standards and flags conflicts for review.", "/design-review → engine: copilot → comment"],
            ["review", "GitHub Copilot code review", "Repository review instructions focus the AI review on architectural gaps. The architect sends findings back for revision before accepting the design.", ".github/instructions/ → targeted ADR review"]
          ]
        },
        {
          name: "Develop", title: "Delegate implementation, not ownership.",
          input: "A bounded feature Issue + acceptance criteria",
          checks: "Scope check + xUnit / Vitest / Playwright CI", decision: "Developer challenges the change, reviews, and merges.",
          recipient: "Test", output: "Reviewable code and tests tied to the requested behavior.",
          steps: [
            ["delegated", "GitHub Copilot cloud agent", "Assign an Issue to develop-github. The agent edits a branch, runs tests in its configured environment, and opens a pull request instead of changing main.", "copilot-setup-steps.yml → .NET / Node / PostgreSQL"],
            ["guidance", "Repository instructions + Agent Skills", "Instructions supply coding and authorization rules; bounded-feature gives the implementation procedure. A separate scope check enforces the allowed change.", "copilot-instructions.md + bounded-feature"],
            ["review", "GitHub Copilot code review", "Request an AI review of the diff and use its findings to guide revisions. The developer still adds independent tests and owns the merge decision.", "Pull request → AI review → developer revision"]
          ]
        },
        {
          name: "Test", title: "Generate regressions. Explain failures.",
          input: "Expected behavior + a reproducible defect",
          checks: "Same regression fails before the fix and passes after it.", decision: "Reviewer accepts the proof, not an AI claim of success.",
          recipient: "Secure & Release", output: "Regression coverage and an evidence-backed fix.",
          steps: [
            ["delegated", "GitHub Copilot cloud agent", "The test-github specialist reproduces the defect and writes API or browser regressions, including retries and concurrency, before applying a fix.", "failure-reproduction → tests-only commit → fix"],
            ["event", "GitHub Agentic Workflows", "On an eligible failed CI run, the Copilot engine compares test messages, the diff, and main’s results. It explains regressions versus expected or infrastructure failures.", "workflow_run: failure → one comment + one label"],
            ["check", "GitHub Actions + test runners", "xUnit, Vitest, and Playwright execute the tests. The test-first proof replays the regression at both commits; the model cannot replace that result.", "Tests-only: FAIL  →  Fixed head: PASS"]
          ]
        },
        {
          name: "Secure", title: "Find risks. Repair within boundaries.",
          input: "A pull request + a confirmed security finding",
          checks: "CodeQL scan + independently authored regression", decision: "Security reviewer decides whether the repair is sufficient.",
          recipient: "Release", output: "A reviewed remediation and a test that prevents recurrence.",
          steps: [
            ["review", "GitHub Copilot code review", "Ask the AI reviewer to examine the pull request for unsafe patterns and explain the code path. Treat its finding as something to investigate, not proof by itself.", "Pull-request diff → finding + code explanation"],
            ["delegated", "GitHub Copilot cloud agent", "Assign the confirmed finding to secure-github. Its remediation skills require a regression first and a narrow repair, without weakening authorization or tests.", "secure-github + verified-remediation"],
            ["check", "CodeQL + trusted replay", "CodeQL performs static analysis, not generative AI. An independent regression is replayed before and after the repair to verify what the agent changed.", "Static analysis + independent FAIL → PASS proof"]
          ]
        },
        {
          name: "Release", title: "Brief the approver. Don’t replace them.",
          input: "A tested release candidate + merged changes",
          checks: "GitHub Actions tests images by digest and verifies checksums.", decision: "Required environment reviewer authorizes publication.",
          recipient: "Operate", output: "An approved release with known changes, risks, and test evidence.",
          steps: [
            ["event", "GitHub Agentic Workflows", "When the candidate succeeds, the Copilot engine summarizes merged changes, test results, and risks for the release approver.", "workflow_run: success → engine: copilot"],
            ["control", "gh-aw safe outputs", "The summary workflow reads collected evidence. Its only allowed write appends a summary to the draft release; it cannot approve or publish.", "safe-outputs: update-release  /  max: 1"],
            ["interactive", "GitHub Copilot CLI", "A release engineer uses release-github to inspect the candidate, verify evidence, or explain a failed run using its logs—not to bypass approval.", "copilot --agent release-github"]
          ]
        },
        {
          name: "Operate", title: "Turn incidents into engineering work.",
          input: "An incident report + logs + repository context",
          checks: "Source-backed triage + regression proof", decision: "Operator validates severity, assigns follow-up, and reviews the fix.",
          recipient: "Plan & Develop", output: "A prioritized follow-up, a regression test, and lessons for the next cycle.",
          steps: [
            ["event", "GitHub Agentic Workflows", "An incident label triggers the Copilot engine to classify severity, separate observations from hypotheses, and propose one bounded follow-up.", "issues: labeled → incident → comment / labels / issue"],
            ["interactive", "GitHub Copilot CLI + Agent Skills", "For operator-led triage, operate-github uses incident-evidence to read logs and code with the operator and build a sourced timeline.", "copilot --agent operate-github"],
            ["delegated", "GitHub Copilot cloud agent", "After the operator assigns the follow-up, the agent uses regression-followup to write a failing test and the smallest fix in a pull request.", "regression-followup → test → fix → human review"]
          ]
        }
      ]
    },
    fr: {
      title: "Cycle de vie logiciel avec l'IA · Le parcours", skip: "Aller au contenu",
      header: "GITHUB / L’IA DANS LE CYCLE LOGICIEL", fullscreen: "Plein écran",
      exitFullscreen: "Quitter le plein écran", repository: "Dépôt",
      eyebrow: "SEPT PHASES. UN CYCLE DE VIE CONNECTÉ.",
      principle: "Où intégrer l’IA. Comment l’utiliser.",
      input: "Point de départ", output: "Transmission", tools: "Zoom sur les technologies",
      checks: "Vérifié par", decision: "Décidé par", sources: "Références technologiques",
      sourceNote: "Ce diaporama présente notre approche, pas une exécution en direct. Les capacités des produits sont documentées ci-dessous ; les contrôles et les relais relèvent de nos choix.",
      speed: "Secondes / étape", play: "Défilement auto", pause: "Pause",
      guardrail: "L'approbation humaine est une limite, pas un raccourci.",
      keyboard: "← → Navigation · Début / Fin · Espace Lecture / Pause",
      previous: "Étape précédente", next: "Étape suivante", nextPhase: "Phase suivante", end: "Fin", nav: "Phases du cycle de vie",
      phase: "PHASE", step: "Étape", inside: "Dans cette phase", handoff: "Décision et relais",
      roles: {app: "IA interactive · application de bureau", interactive: "IA interactive", delegated: "IA déléguée", event: "IA événementielle",
        guidance: "Instructions réutilisables", review: "Revue par l’IA", check: "Automatisation déterministe · sans IA",
        control: "Permissions imposées · sans IA"},
      fullscreenError: "Impossible de changer le mode plein écran. Utilisez la commande de votre navigateur.",
      unavailable: "Le plein écran n'est pas disponible dans ce navigateur.",
      phases: [
        {
          name: "Planifier", title: "De l’intention aux exigences claires.",
          input: "Notes métier + politiques de l’organisation",
          checks: "JSON Schema + vérification des sources", decision: "Le responsable produit approuve le périmètre et tranche les conflits.",
          recipient: "Conception", output: "Exigences partagées, critères d’acceptation et questions ouvertes.",
          steps: [
            ["app", "Application GitHub Copilot · mode Plan", "L’analyste ouvre une session sur le dépôt et demande à Copilot de comparer les notes d’atelier aux règles métier. Le responsable produit tranche les contradictions et fixe le périmètre.", "« Quelles exigences se contredisent ? Cite les deux sources. »"],
            ["guidance", "Agents personnalisés + Agent Skills", "Le profil plan-github définit le rôle. La skill requirements-traceability fournit la méthode pour les citations et les critères vérifiables.", "Rôle : .agent.md  /  Méthode : SKILL.md"],
            ["delegated", "GitHub Copilot cloud agent", "Pour un travail asynchrone, attribuer le ticket au spécialiste. Il propose les exigences dans une pull request que le responsable produit relit.", "Attribution du ticket → plan-github → pull request"]
          ]
        },
        {
          name: "Concevoir", title: "Comparer les options à vos standards.",
          input: "Exigences + standards d’architecture + code existant",
          checks: "Structure de l’ADR + compatibilité OpenAPI", decision: "L’architecte accepte les compromis ; les responsables tranchent les conflits.",
          recipient: "Développement", output: "Une approche acceptée, des limites d’API et des tâches de réalisation.",
          steps: [
            ["app", "Application GitHub Copilot · mode interactif", "À partir du cadrage validé, l’architecte ouvre une session sur le dépôt et compare deux options au regard de l’API existante. Copilot explique les compromis ; l’architecte choisit l’approche.", "« Quelle option préserve le contrat OpenAPI, et pourquoi ? »"],
            ["event", "GitHub Agentic Workflows", "Pour un second avis, l’architecte publie le commentaire /design-review. Le workflow compare la proposition aux règles du dépôt et signale les écarts à examiner.", "/design-review → engine: copilot → commentaire"],
            ["review", "GitHub Copilot code review", "Les instructions de revue du dépôt orientent l’IA vers les lacunes d’architecture. L’architecte demande des révisions avant d’accepter la conception.", ".github/instructions/ → revue ciblée de l’ADR"]
          ]
        },
        {
          name: "Développer", title: "Déléguer le code, pas la responsabilité.",
          input: "Un ticket délimité + des critères d’acceptation",
          checks: "Contrôle du périmètre + CI xUnit / Vitest / Playwright", decision: "Le développeur challenge, relit et fusionne le changement.",
          recipient: "Tests", output: "Du code à relire et des tests liés au comportement demandé.",
          steps: [
            ["delegated", "GitHub Copilot cloud agent", "Attribuer le ticket à develop-github. L’agent code sur une branche, teste dans son environnement configuré et ouvre une pull request sans modifier main.", "copilot-setup-steps.yml → .NET / Node / PostgreSQL"],
            ["guidance", "Instructions du dépôt + Agent Skills", "Les instructions donnent les règles de code et d’autorisation ; bounded-feature guide l’implémentation. Un contrôle distinct impose le périmètre autorisé.", "copilot-instructions.md + bounded-feature"],
            ["review", "GitHub Copilot code review", "Demander une revue IA du diff et exploiter les remarques pour réviser. Le développeur ajoute ses propres tests et garde la décision de fusion.", "Pull request → revue IA → révision humaine"]
          ]
        },
        {
          name: "Tester", title: "Créer les régressions. Expliquer les échecs.",
          input: "Comportement attendu + défaut reproductible",
          checks: "La même régression échoue avant le correctif et passe après.", decision: "Le réviseur accepte la preuve, pas l’affirmation de l’IA.",
          recipient: "Sécurité et livraison", output: "Des tests de régression et un correctif prouvé.",
          steps: [
            ["delegated", "GitHub Copilot cloud agent", "Le spécialiste test-github reproduit le défaut et écrit les régressions API ou navigateur, y compris les reprises et la concurrence, avant de corriger.", "failure-reproduction → commit de tests → correctif"],
            ["event", "GitHub Agentic Workflows", "Sur un échec CI éligible, le moteur Copilot compare les messages de tests, le diff et main. Il distingue régression, échec attendu et problème d’infrastructure.", "workflow_run: failure → commentaire + libellé"],
            ["check", "GitHub Actions + outils de test", "xUnit, Vitest et Playwright exécutent les tests. La preuve rejoue la régression sur les deux commits ; le modèle ne remplace jamais ce résultat.", "Tests seuls : ÉCHEC  →  Correctif : SUCCÈS"]
          ]
        },
        {
          name: "Sécuriser", title: "Détecter les risques. Encadrer la réparation.",
          input: "Une pull request + un problème de sécurité confirmé",
          checks: "Analyse CodeQL + régression écrite indépendamment", decision: "Le responsable sécurité juge si la réparation est suffisante.",
          recipient: "Livraison", output: "Une remédiation relue et un test contre la récidive.",
          steps: [
            ["review", "GitHub Copilot code review", "Demander à l’IA d’examiner les motifs non sûrs et d’expliquer le chemin de code. Un signalement se vérifie : ce n’est pas une preuve en soi.", "Diff de pull request → signalement + explication"],
            ["delegated", "GitHub Copilot cloud agent", "Attribuer le problème confirmé à secure-github. Ses skills imposent un test puis un correctif ciblé, sans affaiblir les autorisations ou les tests.", "secure-github + verified-remediation"],
            ["check", "CodeQL + rejeu de confiance", "CodeQL fait de l’analyse statique, pas de l’IA générative. Une régression indépendante est rejouée avant et après pour vérifier la réparation.", "Analyse statique + preuve indépendante ÉCHEC → SUCCÈS"]
          ]
        },
        {
          name: "Livrer", title: "Éclairer l’approbation, pas la remplacer.",
          input: "Une version candidate testée + les changements fusionnés",
          checks: "GitHub Actions teste les images par empreinte et vérifie les sommes.", decision: "Le réviseur requis de l’environnement autorise la publication.",
          recipient: "Exploitation", output: "Une version approuvée avec ses changements, ses risques et ses preuves.",
          steps: [
            ["event", "GitHub Agentic Workflows", "Après le succès de la version candidate, le moteur Copilot résume les changements, les résultats des tests et les risques pour la personne qui approuve.", "workflow_run: success → engine: copilot"],
            ["control", "gh-aw safe outputs", "Le workflow lit les preuves collectées. Sa seule écriture permise ajoute une synthèse au brouillon de livraison ; il ne peut ni approuver ni publier.", "safe-outputs: update-release  /  max: 1"],
            ["interactive", "GitHub Copilot CLI", "L’ingénieur utilise release-github pour inspecter la version, vérifier les preuves ou expliquer un échec avec les journaux, sans contourner l’approbation.", "copilot --agent release-github"]
          ]
        },
        {
          name: "Exploiter", title: "Transformer l’incident en travail d’ingénierie.",
          input: "Un rapport d’incident + journaux + contexte du dépôt",
          checks: "Triage sourcé + preuve de régression", decision: "L’opérateur valide la gravité, attribue le suivi et examine le correctif.",
          recipient: "Planification et développement", output: "Un suivi priorisé, un test de régression et des leçons pour le prochain cycle.",
          steps: [
            ["event", "GitHub Agentic Workflows", "Le libellé incident déclenche le moteur Copilot : il classe la gravité, distingue faits et hypothèses, puis propose une seule action de suivi délimitée.", "issues: labeled → incident → commentaire / libellés / ticket"],
            ["interactive", "GitHub Copilot CLI + Agent Skills", "Pour un triage piloté par l’opérateur, operate-github utilise incident-evidence afin de lire journaux et code et construire une chronologie sourcée.", "copilot --agent operate-github"],
            ["delegated", "GitHub Copilot cloud agent", "Après l’attribution du suivi, l’agent utilise regression-followup pour écrire un test en échec puis le correctif minimal dans une pull request.", "regression-followup → test → correctif → revue humaine"]
          ]
        }
      ]
    }
  };
  const slugs = ["plan", "design", "develop", "test", "secure", "release", "operate"];
  const icons = ["issue-opened", "git-branch", "git-pull-request", "check-circle", "shield-check", "package", "workflow"];
  const roleIcons = {app: "copilot", interactive: "terminal", delegated: "copilot", event: "workflow",
    guidance: "book", review: "code-review", check: "shield-check", control: "shield-check"};
  const $ = (id) => document.getElementById(id);
  const svg = (name) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    node.classList.add("octicon");
    node.setAttribute("aria-hidden", "true");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", `#icon-${name}`);
    node.append(use);
    return node;
  };
  let language = "en";
  let position = 0;
  let playing = false;
  let timer;
  // One opening, three technology builds, then the decision and handoff.
  const builds = 5;
  const total = slugs.length * builds;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function schedule() {
    window.clearTimeout(timer);
    const fill = $("timer-fill");
    fill.style.transition = "none";
    fill.style.width = "0%";
    if (!playing || document.hidden) return;
    const duration = Number($("speed").value) * 1000;
    if (!reducedMotion.matches) {
      // Flush the reset so a speed or step change starts a fresh progress interval.
      void fill.offsetWidth;
      fill.style.transition = `width ${duration}ms linear`;
      fill.style.width = "100%";
    }
    timer = window.setTimeout(() => {
      if (position === total - 1) {
        setPlaying(false);
      } else {
        go(position + 1);
      }
    }, duration);
  }

  function setPlaying(value) {
    playing = value;
    $("autoplay").setAttribute("aria-pressed", String(value));
    $("play-symbol").textContent = value ? "Ⅱ" : "▶";
    $("play-label").textContent = copy[language][value ? "pause" : "play"];
    schedule();
  }

  function element(tag, cls, value) {
    const node = document.createElement(tag);
    node.className = cls;
    if (value !== undefined) node.textContent = value;
    return node;
  }

  function detail(icon, label, value) {
    const row = element("div", "handoff-row");
    const content = element("div", "handoff-copy");
    content.append(element("span", "handoff-label", label), element("p", "", value));
    row.append(svg(icon), content);
    return row;
  }

  function createChapter(phase, phaseIndex, text) {
    const chapter = element("section", "chapter");
    const title = element("h1", "chapter-title", phase.title);
    title.id = `title-${slugs[phaseIndex]}`;
    chapter.setAttribute("aria-labelledby", title.id);
    const context = element("div", "chapter-context");
    const eyebrow = element("div", "slide-meta");
    eyebrow.append(svg(icons[phaseIndex]), `${text.phase} ${String(phaseIndex + 1).padStart(2, "0")} · ${phase.name}`);
    const rail = element("ol", "build-rail");
    rail.setAttribute("aria-label", text.inside);
    context.append(eyebrow, title, rail);
    const stage = element("div", "build-stage");
    const steps = [
      [text.input, "issue-opened", phase.input, null, null],
      ...phase.steps.map(([role, tech, action, example]) => [text.roles[role], roleIcons[role], tech, action, example]),
      [text.handoff, "git-branch", `${text.output} → ${phase.recipient}`, phase.output, null]
    ];
    steps.forEach(([label, icon, heading, action, example], i) => {
      const number = String(i + 1).padStart(2, "0");
      const item = element("li", "");
      const button = element("button", "build-stop");
      button.type = "button";
      button.append(element("span", "build-node", number),
        element("span", "build-name", i === 0 || i === builds - 1 ? label : heading));
      button.addEventListener("click", () => { setPlaying(false); go(phaseIndex * builds + i); });
      item.append(button);
      rail.append(item);

      const frame = element("div", "build-frame");
      frame.dataset.kind = i === 0 ? "input" : example ? "technology" : "handoff";
      if (example) frame.dataset.role = phase.steps[i - 1][0];
      const meta = element("div", "build-meta");
      meta.append(element("span", "build-label", label), element("span", "build-count", `${text.step} ${number} / ${String(builds).padStart(2, "0")}`));
      frame.append(meta);
      const badge = element("div", "build-icon");
      badge.append(svg(icon));
      frame.append(badge, element("h2", "build-title", heading));
      if (action) frame.append(element("p", "build-action", action));
      if (example) frame.append(element("code", "technical-hook", example));
      if (i === builds - 1) {
        const gates = element("div", "handoff-gates");
        gates.append(detail("check-circle", text.checks, phase.checks), detail("eye", text.decision, phase.decision));
        frame.append(gates);
      }
      stage.append(frame);
      frame.inert = true;
    });
    chapter.append(context, stage);
    chapter.inert = true;
    return chapter;
  }

  function setupDeck() {
    const text = copy[language];
    document.documentElement.lang = language;
    document.title = text.title;
    document.querySelectorAll("[data-text]").forEach((node) => {
      node.textContent = text[node.dataset.text];
    });
    $("language").setAttribute("aria-label", language === "en" ? "Passer en français" : "Switch to English");
    $("phase-nav").setAttribute("aria-label", text.nav);
    const nav = slugs.map((slug, index) => {
      const button = document.createElement("button");
      button.type = "button";
      const number = document.createElement("span");
      number.className = "phase-index";
      number.textContent = String(index + 1).padStart(2, "0");
      const name = document.createElement("span");
      name.className = "phase-name";
      name.append(svg(icons[index]), text.phases[index].name);
      button.append(number, name);
      button.addEventListener("click", () => { setPlaying(false); go(index * builds); });
      return button;
    });
    $("phase-nav").replaceChildren(...nav);
    $("slide").replaceChildren(...text.phases.map((phase, index) => createChapter(phase, index, text)));
    render();
  }

  function render(previous = position) {
    const text = copy[language];
    const phaseIndex = Math.floor(position / builds);
    const step = position % builds;
    const chapters = $("slide").children;
    const chapter = chapters[phaseIndex];
    const oldChapter = chapters[Math.floor(previous / builds)];
    const frames = chapter.querySelectorAll(".build-frame");
    const frame = frames[step];
    Array.from(chapters).forEach((node, i) => {
      node.inert = i !== phaseIndex;
      const button = $("phase-nav").children[i];
      if (i === phaseIndex) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
      button.classList.toggle("completed", i < phaseIndex);
    });
    frames.forEach((node, i) => { node.inert = i !== step; });
    chapter.querySelectorAll(".build-stop").forEach((button, i) => {
      if (i === step) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
      button.classList.toggle("past", i < step);
    });

    // Commit navigation immediately. The outgoing layer is visual only; no callbacks own state.
    $("slide").getAnimations({subtree: true}).forEach(animation => animation.cancel());
    if (previous !== position && !reducedMotion.matches) {
      const forward = position > previous ? 1 : -1;
      const phaseChange = chapter !== oldChapter;
      const incoming = phaseChange ? chapter : frame;
      const outgoing = phaseChange ? oldChapter : frames[previous % builds];
      const offset = (phaseChange ? 40 : 14) * forward;
      const move = n => phaseChange ? `translateX(${n}px)` : `translateY(${n}px)`;
      outgoing.animate([
        {visibility: "visible", opacity: 1, transform: move(0)},
        {visibility: "visible", opacity: 0, transform: move(-offset * .6)}
      ], {duration: 150, easing: "ease-in", fill: "none"});
      incoming.animate([
        {opacity: 0, transform: move(offset)}, {opacity: 1, transform: move(0)}
      ], {duration: phaseChange ? 380 : 280, delay: 80, easing: "cubic-bezier(.2,.8,.2,1)", fill: "backwards"});
    }
    $("position").textContent = `${String(phaseIndex + 1).padStart(2, "0")} / ${String(slugs.length).padStart(2, "0")}`;
    $("previous").disabled = position === 0;
    $("next").disabled = position === total - 1;
    $("previous").setAttribute("aria-label", text.previous);
    $("next").querySelector("span").textContent = $("next").disabled ? text.end : step === builds - 1 ? text.nextPhase : text.next;
    $("play-label").textContent = text[playing ? "pause" : "play"];
    updateFullscreen();
    $("announcement").textContent = `${text.phases[phaseIndex].name}. ${text.step} ${step + 1}. ${frame.querySelector("h2").textContent}`;
    schedule();
  }

  function go(next) {
    const previous = position;
    position = Math.max(0, Math.min(total - 1, next));
    if (position === total - 1) playing = false;
    $("autoplay").setAttribute("aria-pressed", String(playing));
    $("play-symbol").textContent = playing ? "Ⅱ" : "▶";
    render(previous);
  }

  function updateFullscreen() {
    const active = Boolean(document.fullscreenElement);
    $("fullscreen").setAttribute("aria-pressed", String(active));
    $("fullscreen").querySelector("[data-text]").textContent = copy[language][active ? "exitFullscreen" : "fullscreen"];
  }
  $("previous").addEventListener("click", () => { setPlaying(false); go(position - 1); });
  $("next").addEventListener("click", () => { setPlaying(false); go(position + 1); });
  $("language").addEventListener("click", () => {
    language = language === "en" ? "fr" : "en";
    $("error").textContent = "";
    setupDeck();
  });
  $("autoplay").addEventListener("click", () => {
    if (!playing && position === total - 1) go(0);
    setPlaying(!playing);
  });
  $("speed").addEventListener("input", () => {
    $("speed-value").value = `${$("speed").value}s`;
    schedule();
  });
  $("fullscreen").addEventListener("click", async () => {
    $("error").textContent = "";
    if (!document.fullscreenEnabled) {
      $("error").textContent = copy[language].unavailable;
      return;
    }
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch (error) {
      console.error("Slideshow fullscreen failed", error);
      $("error").textContent = copy[language].fullscreenError;
    }
  });
  document.addEventListener("fullscreenchange", updateFullscreen);
  document.addEventListener("visibilitychange", schedule);
  document.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey ||
        event.target.closest("input, select, textarea, [contenteditable]")) return;
    if (event.key === " ") {
      if (event.target.closest("button, a, summary")) return;
      event.preventDefault();
      $("autoplay").click();
    } else if (["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      setPlaying(false);
      go(event.key === "Home" ? 0 : event.key === "End" ? total - 1 : position + (event.key === "ArrowRight" ? 1 : -1));
    }
  });
  reducedMotion.addEventListener("change", () => {
    if (reducedMotion.matches) $("slide").getAnimations({subtree: true}).forEach(animation => animation.cancel());
    schedule();
  });
  setupDeck();
})();
