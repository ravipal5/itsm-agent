const loadSolutionBtn = document.getElementById("load-solution-btn");
const codeEditor = document.getElementById("code-editor");
const languageSelect = document.getElementById("language-select");
const editorThemeSelect = document.getElementById("editor-theme-select");
const generateDsaBtn = document.getElementById("generate-dsa-btn");
const dsaTopicSelect = document.getElementById("dsa-topic-select");
const dsaDifficultySelect = document.getElementById("dsa-difficulty-select");
const dsaGenerateStatus = document.getElementById("dsa-generate-status");
const historyPanel = document.getElementById("history-panel");
const historyStatus = document.getElementById("history-status");
const historyTableBody = document.getElementById("history-table-body");
const historyCountChip = document.getElementById("history-count-chip");
const dsaHistoryPanel = document.getElementById("dsa-history-panel");
const dsaHistoryStatus = document.getElementById("dsa-history-status");
const dsaHistoryTableBody = document.getElementById("dsa-history-table-body");
const dsaHistoryCountChip = document.getElementById("dsa-history-count-chip");

function applyEditorTheme(themeName) {
    if (!codeEditor) {
        return;
    }
    codeEditor.dataset.theme = themeName;
}

function attachLineNumberGutter() {
    if (!codeEditor) {
        return;
    }

    const gutter = document.getElementById("editor-line-numbers");
    if (!gutter) {
        return;
    }

    function renderLineNumbers() {
        const lineCount = Math.max(1, codeEditor.value.split("\n").length);
        gutter.textContent = Array.from({ length: lineCount }, (_, index) => index + 1).join("\n");
    }

    codeEditor.addEventListener("input", renderLineNumbers);
    codeEditor.addEventListener("scroll", () => {
        gutter.scrollTop = codeEditor.scrollTop;
    });
    renderLineNumbers();
}

if (editorThemeSelect) {
    const savedTheme = window.localStorage.getItem("dsa-editor-theme") || "midnight";
    editorThemeSelect.value = savedTheme;
    applyEditorTheme(savedTheme);

    editorThemeSelect.addEventListener("change", () => {
        window.localStorage.setItem("dsa-editor-theme", editorThemeSelect.value);
        applyEditorTheme(editorThemeSelect.value);
    });
}

if (loadSolutionBtn) {
    loadSolutionBtn.addEventListener("click", () => {
        if (!codeEditor) {
            return;
        }

        const language = languageSelect ? languageSelect.value : "python";
        const solutionKey = `${language}Solution`;
        codeEditor.value = loadSolutionBtn.dataset[solutionKey] || "";
        codeEditor.dispatchEvent(new Event("input"));
    });
}

attachLineNumberGutter();

if (historyPanel && historyTableBody) {
    (async () => {
        try {
            const response = await fetch("/interview/history", { headers: { Accept: "application/json" } });
            if (!response.ok) {
                if (historyStatus) {
                    historyStatus.textContent = "Could not load interview history.";
                }
                return;
            }

            const payload = await response.json();
            const reports = payload.reports || [];
            if (historyCountChip) {
                historyCountChip.textContent = `${reports.length} Recent Reports`;
            }
            if (historyStatus) {
                historyStatus.textContent = reports.length
                    ? "Saved interview reports from your previous sessions."
                    : "No saved reports yet. Finish an interview to create your first report.";
            }

            historyTableBody.innerHTML = "";
            if (!reports.length) {
                const row = document.createElement("tr");
                const cell = document.createElement("td");
                cell.colSpan = 6;
                cell.className = "muted-note";
                cell.textContent = "No reports yet.";
                row.appendChild(cell);
                historyTableBody.appendChild(row);
                return;
            }

            reports.forEach((report) => {
                const row = document.createElement("tr");
                const createdAt = report.created_at ? new Date(report.created_at.replace(" ", "T")) : null;
                const createdText = createdAt && !Number.isNaN(createdAt.getTime()) ? createdAt.toLocaleString() : (report.created_at || "-");
                const cells = [
                    createdText,
                    report.role || "-",
                    report.level || "-",
                    report.source || "-",
                    `${report.completion ?? 0}%`,
                    report.overall || "-",
                ];
                cells.forEach((value) => {
                    const td = document.createElement("td");
                    td.textContent = value;
                    row.appendChild(td);
                });
                historyTableBody.appendChild(row);
            });
        } catch {
            if (historyStatus) {
                historyStatus.textContent = "Could not load interview history.";
            }
        }
    })();
}

if (dsaHistoryPanel && dsaHistoryTableBody) {
    (async () => {
        try {
            const response = await fetch("/api/dsa/submissions", { headers: { Accept: "application/json" } });
            if (!response.ok) {
                if (dsaHistoryStatus) {
                    dsaHistoryStatus.textContent = "Could not load DSA submission history.";
                }
                return;
            }

            const payload = await response.json();
            const submissions = payload.submissions || [];
            if (dsaHistoryCountChip) {
                dsaHistoryCountChip.textContent = `${submissions.length} Recent Submissions`;
            }
            if (dsaHistoryStatus) {
                dsaHistoryStatus.textContent = submissions.length
                    ? "Saved submissions from your coding attempts."
                    : "No DSA submissions yet. Open DSA panel and click Submit.";
            }

            dsaHistoryTableBody.innerHTML = "";
            if (!submissions.length) {
                const row = document.createElement("tr");
                const cell = document.createElement("td");
                cell.colSpan = 5;
                cell.className = "muted-note";
                cell.textContent = "No submissions yet.";
                row.appendChild(cell);
                dsaHistoryTableBody.appendChild(row);
                return;
            }

            submissions.forEach((submission) => {
                const row = document.createElement("tr");
                const createdAt = submission.submitted_at ? new Date(submission.submitted_at) : null;
                const createdText = createdAt && !Number.isNaN(createdAt.getTime())
                    ? createdAt.toLocaleString()
                    : (submission.submitted_at || "-");
                const statusText = submission.ok ? "Passed" : "Failed";
                const passedText = submission.ok
                    ? `${submission.passed_count ?? 0}/${submission.total_count ?? 0}`
                    : "-";
                const cells = [
                    createdText,
                    submission.question_title || submission.question_id || "-",
                    (submission.language || "-").toUpperCase(),
                    statusText,
                    passedText,
                ];
                cells.forEach((value) => {
                    const td = document.createElement("td");
                    td.textContent = value;
                    row.appendChild(td);
                });
                dsaHistoryTableBody.appendChild(row);
            });
        } catch {
            if (dsaHistoryStatus) {
                dsaHistoryStatus.textContent = "Could not load DSA submission history.";
            }
        }
    })();
}

if (generateDsaBtn) {
    generateDsaBtn.addEventListener("click", async () => {
        if (dsaGenerateStatus) {
            dsaGenerateStatus.textContent = "Generating a new DSA question.";
        }

        const response = await fetch("/dsa/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic: dsaTopicSelect ? dsaTopicSelect.value : "Array",
                difficulty: dsaDifficultySelect ? dsaDifficultySelect.value : "Medium",
                refresh_token: Date.now(),
            }),
        });

        if (!response.ok) {
            if (dsaGenerateStatus) {
                try {
                    const errPayload = await response.json();
                    dsaGenerateStatus.textContent = errPayload.detail || "Could not generate a new DSA question.";
                } catch {
                    dsaGenerateStatus.textContent = "Could not generate a new DSA question.";
                }
            }
            return;
        }

        const payload = await response.json();
        const language = languageSelect ? languageSelect.value : "python";
        window.location.href = `/dsa/${payload.question_id}?language=${encodeURIComponent(language)}`;
    });
}

const questionsDataNode = document.getElementById("interview-questions-data");
const sessionRoot = document.getElementById("interview-session");

if (questionsDataNode && sessionRoot) {
    let questions = JSON.parse(questionsDataNode.textContent || "[]");
    let profile = JSON.parse(sessionRoot.dataset.profile || "{}");
    const interviewSource = sessionRoot.dataset.interviewSource || "skills";
    const currentQuestionText = document.getElementById("current-question-text");
    const voiceCaption = document.getElementById("voice-caption");
    const interviewProgress = document.getElementById("interview-progress");
    const interviewStatus = document.getElementById("interview-status");
    const transcriptField = document.getElementById("voice-transcript");
    const savedAnswerLog = document.getElementById("saved-answer-log");
    const startInterviewBtn = document.getElementById("start-interview-btn");
    const repeatQuestionBtn = document.getElementById("repeat-question-btn");
    const startAnswerBtn = document.getElementById("start-answer-btn");
    const stopAnswerBtn = document.getElementById("stop-answer-btn");
    const nextQuestionBtn = document.getElementById("next-question-btn");
    const finishInterviewBtn = document.getElementById("finish-interview-btn");
    const regenerateQuestionsBtn = document.getElementById("regenerate-questions-btn");
    const questionLevelSelect = document.getElementById("question-level-select");
    const currentLevelLabel = document.getElementById("current-level-label");
    const feedbackPanel = document.getElementById("feedback-panel");
    const feedbackScore = document.getElementById("feedback-score");
    const feedbackOverall = document.getElementById("feedback-overall");
    const feedbackStrengths = document.getElementById("feedback-strengths");
    const feedbackImprovements = document.getElementById("feedback-improvements");
    const feedbackRecommendation = document.getElementById("feedback-recommendation");
    const answerLiveCaption = document.getElementById("answer-live-caption");
    const planHeadline = document.getElementById("plan-headline");
    const planStages = document.getElementById("plan-stages");
    const planStyle = document.getElementById("plan-style");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const hasSpeechSynthesis = "speechSynthesis" in window;
    let questionAnswers = questions.map((item) => ({ question: item.question, type: item.type, answer: "" }));
    let currentIndex = -1;
    let interviewStarted = false;
    let isRecording = false;
    let latestTranscript = "";
    let recognition = null;

    function setStatus(text) {
        if (interviewStatus) {
            interviewStatus.textContent = text;
        }
    }

    function setButtonState(button, enabled) {
        if (!button) {
            return;
        }
        button.disabled = !enabled;
        button.style.opacity = enabled ? "1" : "0.55";
        button.style.cursor = enabled ? "pointer" : "not-allowed";
    }

    function refreshControlState() {
        const hasQuestions = questions.length > 0;
        const hasActiveQuestion = interviewStarted && currentIndex >= 0 && currentIndex < questions.length;
        const hasNext = hasActiveQuestion && currentIndex + 1 < questions.length;
        setButtonState(startInterviewBtn, hasQuestions);
        setButtonState(repeatQuestionBtn, hasActiveQuestion);
        setButtonState(startAnswerBtn, hasActiveQuestion);
        setButtonState(stopAnswerBtn, hasActiveQuestion && isRecording);
        setButtonState(nextQuestionBtn, hasNext);
        setButtonState(finishInterviewBtn, hasActiveQuestion);
    }

    function renderInterviewPlan(plan, level) {
        if (!plan) {
            return;
        }

        if (planHeadline) {
            planHeadline.textContent = plan.headline || `${level || "Junior"} interview with a human interviewer style.`;
        }
        if (planStages) {
            planStages.innerHTML = "";
            (plan.stages || []).forEach((item) => {
                const li = document.createElement("li");
                li.textContent = item;
                planStages.appendChild(li);
            });
        }
        if (planStyle) {
            planStyle.textContent = plan.interviewer_style || "";
        }
    }

    function rebuildAnswersState() {
        questionAnswers = questions.map((item) => ({ question: item.question, type: item.type, answer: "" }));
        currentIndex = -1;
        interviewStarted = false;
        latestTranscript = "";
        if (transcriptField) {
            transcriptField.value = "";
        }
        if (savedAnswerLog) {
            savedAnswerLog.value = "";
        }
        if (currentQuestionText) {
            currentQuestionText.textContent = "Click Start Interview to begin.";
        }
        if (voiceCaption) {
            voiceCaption.textContent = "Only the current question will appear here while the interviewer is speaking.";
        }
        if (answerLiveCaption) {
            answerLiveCaption.textContent = "Start Answer to see your live speech caption here.";
        }
        updateProgress();
        refreshControlState();
    }

    function renderSavedAnswers() {
        if (!savedAnswerLog) {
            return;
        }

        savedAnswerLog.value = questionAnswers
            .filter((item) => item.answer.trim())
            .map((item, index) => `Q${index + 1}: ${item.question}\nA: ${item.answer.trim()}`)
            .join("\n\n");
    }

    function updateProgress() {
        if (interviewProgress) {
            const shownIndex = currentIndex >= 0 ? currentIndex + 1 : 0;
            interviewProgress.textContent = `Question ${shownIndex} of ${questions.length}`;
        }
    }

    function stopSpeaking() {
        if (hasSpeechSynthesis) {
            window.speechSynthesis.cancel();
        }
    }

    function speakQuestion(index) {
        if (index < 0 || index >= questions.length) {
            return;
        }

        const text = questions[index].question;
        if (currentQuestionText) {
            currentQuestionText.textContent = text;
        }
        if (voiceCaption) {
            voiceCaption.textContent = text;
        }

        if (!hasSpeechSynthesis) {
            setStatus("Current question is on screen. Voice playback is not supported in this browser.");
            return;
        }

        stopSpeaking();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.94;
        utterance.pitch = 1;
        utterance.onstart = () => setStatus("Interviewer is asking the current question.");
        utterance.onend = () => setStatus("Question finished. Speak your answer when you are ready.");
        window.speechSynthesis.speak(utterance);
    }

    function saveCurrentAnswer() {
        if (currentIndex < 0 || currentIndex >= questionAnswers.length || !transcriptField) {
            return;
        }

        questionAnswers[currentIndex].answer = transcriptField.value.trim();
        renderSavedAnswers();
    }

    function moveToQuestion(index) {
        currentIndex = index;
        updateProgress();
        if (transcriptField) {
            transcriptField.value = questionAnswers[index].answer || "";
        }
        latestTranscript = transcriptField ? transcriptField.value : "";
        speakQuestion(index);
        refreshControlState();
    }

    function startRecognition() {
        if (!recognition || !transcriptField) {
            if (transcriptField) {
                transcriptField.value = "Speech recognition is not supported in this browser.";
            }
            return;
        }

        latestTranscript = transcriptField.value.trim();
        recognition.start();
    }

    function stopRecognition() {
        if (recognition && isRecording) {
            recognition.stop();
        }
        refreshControlState();
    }

    async function generateFeedback() {
        saveCurrentAnswer();
        setStatus("Generating interview feedback.");

        const response = await fetch("/interview/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                profile,
                question_answers: questionAnswers,
            }),
        });

        if (!response.ok) {
            setStatus("Could not generate feedback.");
            return;
        }

        const feedback = await response.json();
        if (feedbackPanel) {
            feedbackPanel.hidden = false;
        }
        if (feedbackScore) {
            feedbackScore.textContent = `Completion ${feedback.completion}%`;
        }
        if (feedbackOverall) {
            feedbackOverall.textContent = feedback.overall || "";
        }
        if (feedbackRecommendation) {
            feedbackRecommendation.textContent = feedback.recommendation || "";
        }

        if (feedbackStrengths) {
            feedbackStrengths.innerHTML = "";
            (feedback.strengths || []).forEach((item) => {
                const li = document.createElement("li");
                li.textContent = item;
                feedbackStrengths.appendChild(li);
            });
        }

        if (feedbackImprovements) {
            feedbackImprovements.innerHTML = "";
            (feedback.improvements || []).forEach((item) => {
                const li = document.createElement("li");
                li.textContent = item;
                feedbackImprovements.appendChild(li);
            });
        }

        setStatus("Interview finished. Feedback is ready.");
    }

    async function regenerateQuestions() {
        stopRecognition();
        stopSpeaking();
        setStatus("Generating a fresh interview set.");
        setButtonState(regenerateQuestionsBtn, false);

        try {
            const requestedLevel = questionLevelSelect ? questionLevelSelect.value : (profile.experience_level || "Junior");
            const response = await fetch(`/interview/questions?ts=${Date.now()}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    profile,
                    interview_source: interviewSource,
                    experience_level: requestedLevel,
                    refresh_token: Date.now(),
                    previous_questions: questions.map((item) => item.question),
                }),
            });

            if (!response.ok) {
                setStatus("Could not generate a new question set.");
                return;
            }

            const payload = await response.json();
            const nextQuestions = payload.questions || [];
            if (!nextQuestions.length) {
                setStatus(payload.profile?.generation_error || "Gemini did not return new questions. Please try again.");
                return;
            }
            questions = nextQuestions;
            profile = payload.profile || profile;
            renderInterviewPlan(payload.interview_plan, profile.experience_level || requestedLevel);
            if (currentLevelLabel) {
                currentLevelLabel.textContent = profile.experience_level || requestedLevel;
            }
            rebuildAnswersState();
            if (feedbackPanel) {
                feedbackPanel.hidden = true;
            }
            if (profile.generation_source === "gemini") {
                setStatus("New Gemini interview questions are ready. Start when you want.");
            } else {
                setStatus(profile.generation_error || "Gemini did not generate questions, so fallback questions were used.");
            }
        } finally {
            setButtonState(regenerateQuestionsBtn, true);
        }
    }

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onstart = () => {
            isRecording = true;
            setStatus("Listening for your answer.");
            if (answerLiveCaption) {
                answerLiveCaption.textContent = "Listening...";
            }
            refreshControlState();
        };

        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map((result) => result[0].transcript)
                .join(" ")
                .trim();
            latestTranscript = transcript;
            if (transcriptField) {
                transcriptField.value = transcript;
            }
            if (answerLiveCaption) {
                answerLiveCaption.textContent = transcript || "Listening...";
            }
        };

        recognition.onend = () => {
            isRecording = false;
            if (transcriptField && latestTranscript) {
                transcriptField.value = latestTranscript;
            }
            if (answerLiveCaption) {
                answerLiveCaption.textContent = latestTranscript || "Answer capture stopped.";
            }
            saveCurrentAnswer();
            setStatus("Answer capture stopped.");
            refreshControlState();
        };
    }

    if (startInterviewBtn) {
        startInterviewBtn.addEventListener("click", () => {
            if (!questions.length) {
                setStatus("No interview questions are available.");
                return;
            }

            interviewStarted = true;
            if (feedbackPanel) {
                feedbackPanel.hidden = true;
            }
            moveToQuestion(0);
            refreshControlState();
        });
    }

    if (repeatQuestionBtn) {
        repeatQuestionBtn.addEventListener("click", () => {
            if (!interviewStarted || currentIndex < 0) {
                setStatus("Start the interview first.");
                return;
            }
            speakQuestion(currentIndex);
        });
    }

    if (startAnswerBtn) {
        startAnswerBtn.addEventListener("click", () => {
            if (!interviewStarted || currentIndex < 0) {
                setStatus("Start the interview first.");
                return;
            }
            startRecognition();
        });
    }

    if (stopAnswerBtn) {
        stopAnswerBtn.addEventListener("click", () => {
            stopRecognition();
        });
    }

    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener("click", () => {
            if (!interviewStarted || currentIndex < 0) {
                setStatus("Start the interview first.");
                return;
            }

            stopRecognition();
            stopSpeaking();
            saveCurrentAnswer();
            if (currentIndex + 1 >= questions.length) {
                generateFeedback();
                return;
            }
            moveToQuestion(currentIndex + 1);
        });
    }

    if (finishInterviewBtn) {
        finishInterviewBtn.addEventListener("click", () => {
            if (!interviewStarted) {
                setStatus("Start the interview first.");
                return;
            }

            stopRecognition();
            stopSpeaking();
            generateFeedback();
        });
    }

    if (regenerateQuestionsBtn) {
        regenerateQuestionsBtn.addEventListener("click", regenerateQuestions);
    }

    rebuildAnswersState();
    refreshControlState();
}
