window.addEventListener("load", (event) => {
    console.log("Hello Gemini Realtime Demo!");

    setAvailableMicrophoneOptions();
});

const PROXY_URL = window.ENV?.BACKEND_URL || "ws://localhost:8080";
const PROJECT_ID = window.ENV?.PROJECT_ID || "gen-lang-client-0427088816";
const MODEL = window.ENV?.MODEL || "gemini-2.0-flash-live-preview-04-09";
const API_HOST = window.ENV?.API_HOST || "us-central1-aiplatform.googleapis.com";

const systemInstructionsInput = document.getElementById("systemInstructions");

CookieJar.init("systemInstructions");

const disconnected = document.getElementById("disconnected");
const connecting = document.getElementById("connecting");
const connected = document.getElementById("connected");
const speaking = document.getElementById("speaking");

const micBtn = document.getElementById("micBtn");
const micOffBtn = document.getElementById("micOffBtn");

const micSelect = document.getElementById("audioSource");

const geminiLiveApi = new GeminiLiveAPI(PROXY_URL, PROJECT_ID, MODEL, API_HOST);

geminiLiveApi.onErrorMessage = (message) => {
    showDialogWithMessage(message);
    setAppStatus("disconnected");
};

function getSelectedResponseModality() {
    // return "AUDIO";
    const radioButtons = document.querySelectorAll(
        'md-radio[name="responseModality"]',
    );

    let selectedValue;
    for (const radioButton of radioButtons) {
        if (radioButton.checked) {
            selectedValue = radioButton.value;
            break;
        }
    }
    return selectedValue;
}

function getSystemInstructions() {
    return systemInstructionsInput.value;
}

function connectBtnClick() {
    setAppStatus("connecting");

    geminiLiveApi.responseModalities = getSelectedResponseModality();
    geminiLiveApi.systemInstructions = getSystemInstructions();

    geminiLiveApi.onConnectionStarted = () => {
        setAppStatus("connected");
        startAudioInput();
    };

    geminiLiveApi.connect();
}

const liveAudioOutputManager = new LiveAudioOutputManager();

geminiLiveApi.onReceiveResponse = (messageResponse) => {
    if (messageResponse.type == "AUDIO") {
        liveAudioOutputManager.playAudioChunk(messageResponse.data);
    } else if (messageResponse.type == "TEXT") {
        console.log("Gemini said: ", messageResponse.data);
        newModelMessage(messageResponse.data);
    } else if (messageResponse.type == "INPUT_TRANSCRIPTION") {
        console.log("User said: ", messageResponse.data);
        addTranscriptionMessage("User", messageResponse.data);
    } else if (messageResponse.type == "OUTPUT_TRANSCRIPTION") {
        console.log("Gemini transcription: ", messageResponse.data);
        addTranscriptionMessage("Gemini", messageResponse.data);
    }
};

const liveAudioInputManager = new LiveAudioInputManager();

liveAudioInputManager.onNewAudioRecordingChunk = (audioData) => {
    geminiLiveApi.sendAudioMessage(audioData);
};

function addMessageToChat(message) {
    const textChat = document.getElementById("text-chat");
    const newParagraph = document.createElement("p");
    newParagraph.textContent = message;
    textChat.appendChild(newParagraph);
}

function addTranscriptionMessage(speaker, message) {
    const textChat = document.getElementById("text-chat");
    const newParagraph = document.createElement("p");
    newParagraph.textContent = `[${speaker} Transcription]: ${message}`;
    newParagraph.style.fontStyle = "italic";
    newParagraph.style.color = speaker === "User" ? "#0066cc" : "#cc6600";
    textChat.appendChild(newParagraph);
}

function newModelMessage(message) {
    addMessageToChat(">> " + message);
}

function startAudioInput() {
    liveAudioInputManager.connectMicrophone();
}

function stopAudioInput() {
    liveAudioInputManager.disconnectMicrophone();
}

function micBtnClick() {
    console.log("micBtnClick");
    stopAudioInput();
    micBtn.hidden = true;
    micOffBtn.hidden = false;
}

function micOffBtnClick() {
    console.log("micOffBtnClick");
    startAudioInput();

    micBtn.hidden = false;
    micOffBtn.hidden = true;
}

function newMicSelected() {
    console.log("newMicSelected", micSelect.value);
    liveAudioInputManager.updateMicrophoneDevice(micSelect.value);
}

function disconnectBtnClick() {
    setAppStatus("disconnected");
    geminiLiveApi.disconnect();
    stopAudioInput();
}

function showDialogWithMessage(messageText) {
    const dialog = document.getElementById("dialog");
    const dialogMessage = document.getElementById("dialogMessage");
    dialogMessage.innerHTML = messageText;
    dialog.show();
}

async function getAvailableDevices(deviceType) {
    const allDevices = await navigator.mediaDevices.enumerateDevices();
    const devices = [];
    allDevices.forEach((device) => {
        if (device.kind === deviceType) {
            devices.push({
                id: device.deviceId,
                name: device.label || device.deviceId,
            });
        }
    });
    return devices;
}

async function getAvailableAudioInputs() {
    return await this.getAvailableDevices("audioinput");
}

function setMaterialSelect(allOptions, selectElement) {
    allOptions.forEach((optionData) => {
        const option = document.createElement("md-select-option");
        option.value = optionData.id;

        const slotDiv = document.createElement("div");
        slotDiv.slot = "headline";
        slotDiv.innerHTML = optionData.name;
        option.appendChild(slotDiv);

        selectElement.appendChild(option);
    });
}

async function setAvailableMicrophoneOptions() {
    const mics = await getAvailableAudioInputs();
    const audioSelect = document.getElementById("audioSource");
    setMaterialSelect(mics, audioSelect);
}

function setAppStatus(status) {
    disconnected.hidden = true;
    connecting.hidden = true;
    connected.hidden = true;
    speaking.hidden = true;

    switch (status) {
        case "disconnected":
            disconnected.hidden = false;
            break;
        case "connecting":
            connecting.hidden = false;
            break;
        case "connected":
            connected.hidden = false;
            break;
        case "speaking":
            speaking.hidden = false;
            break;
        default:
    }
}
