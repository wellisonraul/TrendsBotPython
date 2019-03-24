from os import environ
import json
from string import punctuation
from googleapiclient import http, discovery
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from telegram import ext
from nltk.tokenize import wordpunct_tokenize
from emoji import emojize
from requests import post, get
from bs4 import BeautifulSoup

# Váriavel de ambiente from git
bot_key = environ['BOT_KEY']
client = speech.SpeechClient()


def normalizar(frase):
    """ Normalização da frase
        Parâmetro:
            frase: frase de entrada do usuário original

        Saída:
            frase_normalizada: frase normalizada para pesquisa
    """
    remocao = set([palavra.strip() for palavra in open("stopwords.txt")])
    frase_sem_palavras = [palavra.lower() for palavra in wordpunct_tokenize(frase) if palavra not in remocao]
    frase_normalizada = " ".join(token for token in frase_sem_palavras if not pontuacao(token))  # Remova pontuação
    return frase_normalizada


def pontuacao(frase):
    """ Normalização da frase
        Parâmetro:
            frase: frase de entrada já processada

        Saída:
            Return: frase normalizada sem pontuação!
    """
    return all([char in punctuation for char in frase])


# GCloud Procesamento de áudio
# create_service, upload_object são métodos padrões de tratamento de dados entre o Python e Cloud.
def create_service():
    return discovery.build('storage', 'v1')


def upload_object(bucket, filename, readers="", owners=""):
    service = create_service()

    body = {
        'name': filename,
    }

    if readers or owners:
        body['acl'] = []

    for r in readers:
        body['acl'].append({
            'entity': 'user-%s' % r,
            'role': 'READER',
            'email': r
        })
    for o in owners:
        body['acl'].append({
            'entity': 'user-%s' % o,
            'role': 'OWNER',
            'email': o
        })

    with open(filename, 'rb') as f:
        req = service.objects().insert(
            bucket=bucket, body=body,
            media_body=http.MediaIoBaseUpload(
                f, 'video/ogg'))
        resp = req.execute()

    return resp


def transcricao_audio():
    """ Transcrever um áudio que está na Cloud.
        Saída:
            Return:Áudio transcrito
    """
    create_service()
    upload_object("sdbot", "voice.ogg")
    audio = types.RecognitionAudio(uri='gs://sdbot/voice.ogg')
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=16000,
        language_code='pt-BR')

    return client.recognize(config, audio)


# Acessar o engenho Golang
def requisitar_twitter(texto_normalizado):
    """ Requisitar a API para análise de sentimentos e requisitar o Twitter
        Parâmetro:
            texto_normaliza: texto processado pelo normalizar

        Saída:
            Return: Conjunto de Twitters!
    """
    payload = {'text': texto_normalizado, 'tweets_sample_size': 2}
    headers = {'content-type': 'application/json'}
    r = post('http://localhost:8080/text', data=json.dumps(payload), headers=headers)
    return dict(r.json())


def montar_messagem_usuario(retorno_twitter, jornal_twitter, lista_g1):
    """ Informar ao usuário o final do processamento!
        Parâmetro:
            retorno_twitter: retorno da API de consulta GO

        Saída:
            retorno_usuario: Mensagem informando resutlado do processamento!
    """
    retorno_usuario = ""
    if 'name' in retorno_twitter:
        if retorno_twitter['tweet_volume'] != 0:
            retorno_usuario = "Foram encontrados " + str(
                retorno_twitter['tweet_volume']) + " publicações sobre o tema: " + retorno_twitter[
                                  'name'] + " :relieved:"
        elif retorno_twitter['tweet_volume'] == 0:
            retorno_usuario = "Infelizmente :broken_heart:, o Twitter não disponibilizou as informações sobre a" \
                              " quantidade de publicações para o tema: " + retorno_twitter['name']
        if retorno_twitter['sentiment_score'] < -0.05:
            retorno_usuario = retorno_usuario + ". As pessoas apresentam sentimentos negativos para este tema. :rage:\n"
        elif retorno_twitter['sentiment_score'] > 0.05:
            retorno_usuario = retorno_usuario + ". As pessoas apresentam sentimentos positivos para este tema. " \
                                                ":heart_eyes:\n "
        elif 0.05 >= retorno_twitter['sentiment_score'] >= -0.05:
            retorno_usuario = retorno_usuario + ". As pessoas apresentam sentimentos neutros para este tema. " \
                                                ":kissing:\n "

        retorno_usuario = retorno_usuario + "Eu selecionei algumas publicações sobre esse tema: \n"
        for tweet in retorno_twitter['sample_tweets']:
            retorno_usuario = retorno_usuario + "\nPublicação selecionada: \n"
            retorno_usuario = retorno_usuario + tweet + "\n"
    else:
        retorno_usuario = "Infelizmente, o tema pesquisado não está disponível nos Trending Topics do Twitter! " \
                          ":broken_heart:"

    retorno_usuario_g1 = ""
    retorno_usuario_bbc = ""
    retorno_usuario_diario = ""
    if jornal_twitter[0]:
        retorno_usuario_g1 = "\n\nNo Twitter do G1 você pode encontrar: " + str(jornal_twitter[0])
    if jornal_twitter[1]:
        retorno_usuario_bbc = "\n\nNo Twitter da BBC você pode encontrar: " + str(jornal_twitter[1])
    if jornal_twitter[2]:
        retorno_usuario_diario = "\n\nNo Twitter do Diário você pode encontrar: " + str(jornal_twitter[2])

    if retorno_usuario_g1 or retorno_usuario_bbc or retorno_usuario_diario:
        retorno_twiter_jornal = "\n\nVamos procurar informações recentes nos Twitters de grandes portais:" \
                                + retorno_usuario_g1 + retorno_usuario_bbc + retorno_usuario_diario
    else:
        retorno_twiter_jornal = "\n\nO twitter do G1, BBC news e do Diário do Pernambcuo também não apresentam " \
                                "recentemente informações sobre este fato!"

    retorno_usuario_g1_site = ""
    for site in lista_g1:
        retorno_usuario_g1_site = retorno_usuario_g1_site + ' \n\n ' + site

    if retorno_usuario_g1_site:
        retorno_usuario_g1_site = '\n\nO site do #G1 tem matéria(s) que pode(m) ser útil(eis) para elucidar ' \
                                  'a questão: ' + retorno_usuario_g1_site + ' Você pode encontrá-la no link: ' \
                                                                            'https://g1.globo.com/fato-ou-fake/'
    else:
        retorno_usuario_g1_site = "\n\nO portal #G1 não apresenta matéria sobre este fato!"

    return retorno_usuario + retorno_twiter_jornal + retorno_usuario_g1_site


def iniciar(bot, update):
    """ Como usar este bot?
        Parâmetro:
            bot: Cliente de conversa com o bot
            update: Informações sobre a requisição do cliente
    """

    bot.send_message(chat_id=update.message.chat_id,
                     text='Para ter um áudio processado você precisar '
                          'dizer a palavra Twitter no ínicio da frase. '
                          'Para ter um texto processado você precisa usar o comando /twitter. '
                          'Para descobrir as tendências do Brasil digite /tts ou envie sua localização '
                          'para determinar as suas tendências regionais.')


def tts(bot, update):
    """ Receba os Trends Topics atuais no Brasil
        Parâmetro:
            bot: Cliente de conversa com o bot
            update: Informações sobre a requisição do cliente
    """
    tts_req = requisicao_twitter()
    tts_req = "Os tópicos requisitados foram do local: Brasil!\n" + tts_req
    bot.send_message(chat_id=update.message.chat_id,
                     text=tts_req)


def requisicao_twitter():
    """ Requisite a API do GoLang receba os Trends Topics do Brasil
        Parâmetro:
            bot: Cliente de conversa com o bot
            update: Informações sobre a requisição do cliente

        Saída:
            Resposta ao usuário: Texto contendo resultado da solicitação.
    """
    r = get('http://localhost:8080/tts/23424768')
    tts_req = r.json()

    tt_dict_original = {}
    for i in tts_req['trends']:
        if i['tweet_volume'] != 0:
            tt_dict_original[i['name']] = i['tweet_volume']

    tt_dict_personalizado = {}
    for item in sorted(tt_dict_original, key=tt_dict_original.get, reverse=True):
        tt_dict_personalizado[item] = tt_dict_original[item]

    resposta_usuario = ""
    index = 0
    for item in tt_dict_personalizado:
        if index <= 9:
            resposta_usuario = resposta_usuario + str(item) + \
                               " com " + str(tt_dict_personalizado[item]) + " publicações!\n"
        index = index + 1
    return resposta_usuario


def pegar_twitter_jornal(texto_normalizado, jornais):
    """ Pegar Twitter relacionados a pesquisa usando portais de noticias
        Parâmetro:
            texto_normalizado: texto de busca normalizado
            jornais: Jornais para busca no Twitter

        Saída:
            lista_resultados: Texto contendo resultado da solicitação.
    """
    lista_resultados = []
    for jornal in jornais:
        texto_normalizado = texto_normalizado.lower()
        texto_split = texto_normalizado.split()
        get_jornal = get('http://localhost:8080/text2/' + str(jornal))
        tweet_jornal = get_jornal.json()
        for tweet in tweet_jornal['sample_tweets']:
            for palavra in texto_split:
                if palavra in tweet.lower():
                    lista_resultados.append([jornal, tweet])
    g1 = []
    for index in range(0, len(lista_resultados)):
        if lista_resultados[index][0] == 'g1':
            g1 = lista_resultados[index][1]
            break
    bbcbrasil = []
    for index in range(0, len(lista_resultados)):
        if lista_resultados[index][0] == 'bbcbrasil':
            bbcbrasil = lista_resultados[index][1]
            break

    diario = []
    for index in range(0, len(lista_resultados)):
        if lista_resultados[index][0] == 'DiarioPE':
            diario = lista_resultados[index][1]
            break

    lista = [g1, bbcbrasil, diario]
    return lista


def pegar_site_jornal(texto_normalizado):
    """ Buscar informações na página do G1 da frase
        Parâmetro:
            frase: frase de entrada já processada

            Saída:
                lista_final: Nóticias que colodiram com o texto normalizado
        """
    url = 'https://g1.globo.com/fato-ou-fake/'
    get_html = get(url)
    soup = BeautifulSoup(get_html.content, 'html.parser')
    tabelas = soup.findAll("a")

    lista_resultados = []
    for index in tabelas:
        try:
            if index['class'] == ['feed-post-link', 'gui-color-primary', 'gui-color-hover']:
                lista_resultados.append(index.text)
        except:
            continue

    texto_split = texto_normalizado.split()
    lista_final = []
    for resultado in lista_resultados:
        for palavra in texto_split:
            if palavra in resultado.lower():
                lista_final.append(resultado)

    return lista_final


def twitter(bot, update):
    """ Processe a solicitação /twitter realizada via chat pelo bot
        1. Receba a mensagem e remova o /twitter
        2. Informa ao usuário o recebimento da mensagem
        3. Normalize a mensagem
        4. Pré-processar a mensagem
        5. Requisite a API Go Lang
        6. Devolva a mensagem ao usuário

            Parâmetro:
                update: Informações sobre a requisição do cliente

            Saída:
                Faça o bot responder ao usuário
    """
    messagem = update.message['text']
    if messagem.startswith("/twitter"):
        messagem = messagem.replace("/twitter", "")
        usuario = update.message.from_user
        update.message.reply_text("Olá " + usuario['first_name'] + "\nRecebi sua mensagem: "
                                  + messagem + "\nEstou processando sua solicitação agora!")
        messagem = messagem.lower()

        texto_normalizado = normalizar(messagem)
        retorno_twitter = requisitar_twitter(texto_normalizado)
        jornal_twitter = pegar_twitter_jornal(texto_normalizado, ['g1', 'bbc', 'DiarioPE'])
        lista_g1 = pegar_site_jornal(texto_normalizado)
        update.message.reply_text(
            emojize(montar_messagem_usuario(retorno_twitter, jornal_twitter, lista_g1), use_aliases=True))


def voz(bot, update):
    """Processe a solicitação /twitter realizada via chat pelo bot
            1. Baixe o áudio e salve na Cloud
            2. Processe o áudio usando o Google Speech
            3. Receba a mensagem e remova o /twitter
            4. Informa ao usuário o recebimento da mensagem
            5. Normalize a mensagem
            6. Pré-processar a mensagem
            7. Requisite a API Go Lang
            8. Devolva a mensagem ao usuário

        Parâmetro:
            bot: receba as informações do bot
                update: Informações sobre a requisição do cliente
        Saída:
            Faça o bot responder ao usuário
    """
    arquivo_id = update.message.voice.file_id
    novo_arquivo = bot.get_file(arquivo_id)
    novo_arquivo.download('voice.ogg')
    transcricao_speech = transcricao_audio()
    texto_speech = transcricao_speech.results[0].alternatives[0].transcript

    if texto_speech.startswith("Twitter"):
        texto_speech = texto_speech.replace("Twitter", "")
        usuario = update.message.from_user

        update.message.reply_text("Olá " + usuario['first_name'] + "\nRecebi sua mensagem: "
                                  + texto_speech + "\nEstou processando sua solicitação agora!")
        texto_speech = texto_speech.lower()
        texto_normalizado = normalizar(texto_speech)
        retorno_twitter = requisitar_twitter(texto_normalizado)
        jornal_twitter = pegar_twitter_jornal(texto_normalizado, ['g1', 'bbc', 'DiarioPE'])
        lista_g1 = pegar_site_jornal(texto_normalizado)
        update.message.reply_text(
            emojize(montar_messagem_usuario(retorno_twitter, jornal_twitter, lista_g1), use_aliases=True))


def main():
    """ Inicie o bot e habilite o reconhecimento dos comandos iniciar,
        twitter e tts. Além disso, permita a identificação de áudio
        enviado ao grupo.
    """
    updater = ext.Updater(bot_key)
    dp = updater.dispatcher
    dp.add_handler(ext.MessageHandler(ext.Filters.voice, voz))
    dp.add_handler(ext.CommandHandler('iniciar', iniciar))
    dp.add_handler(ext.CommandHandler('twitter', twitter))
    dp.add_handler(ext.CommandHandler('tts', tts))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
