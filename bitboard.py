import web
from bitmessage_gateway import gateway_instance as nexus
import config
import math
import themes

t_globals = dict(
    math=math,
    bitmessage=nexus,
    datestr=web.datestr,
    themes=themes.themes,
    config=config)

urls = (
    '/delete/*(.+)', 'Delete',
    '/images/*(.+)', 'Images',
    '/join/*(.+)', 'Join',
    '/board/*(.+)', 'Board',
    '/catalog/*(.+)', 'Catalog',
    '/thread/*(.+)', 'Thread',
    '/*(.+)', 'Index'
)

render = web.template.render('templates/', cache=config.cache, globals=t_globals)
render._keywords['globals']['render'] = render
render._keywords['globals']['bitmessage'] = nexus
app = web.application(urls, globals())
app.daemon = True
app.internalerror = web.debugerror


class Delete:
    def __init__(self):
        pass

    def GET(self, url):
        web_input = web.input(chan=None, threadid=None, messageid=None)

        render._keywords['globals']['model'] = {"current_thread": web_input.threadid,
                                                "current_chan": web_input.chan}

        render._keywords['globals']['model']['status_message'] = None

        if web_input.messageid:
            result = nexus.deleteMessage(web_input.chan, web_input.messageid)
            render._keywords['globals']['model']['status_message'] = result
            render._keywords['globals']['model']['status_title'] = "Deleted Message"

        if web_input.threadid:
            result = nexus.deleteThread(web_input.chan, web_input.threadid)
            render._keywords['globals']['model']['status_message'] = result
            render._keywords['globals']['model']['status_title'] = "Deleted Thread"

        return render.base(render.pages.alert())


class Images:
    def __init__(self):
        pass

    def GET(self, url):
        web_input = web.input(image=None)
        return nexus.getImage(web_input.image)


class Join:
    def __init__(self):
        pass

    def POST(self, url):
        web_input = web.input(chan=None, passphrase=None)

        render._keywords['globals']['model'] = {"current_chan": web_input.chan}
        result = nexus.joinChan(web_input.passphrase)

        render._keywords['globals']['model']['status_title'] = "Success"
        render._keywords['globals']['model']['status_message'] = result

        return render.base(render.pages.alert())


class Board:
    def __init__(self):
        pass

    def GET(self, url):
        web_input = web.input(chan=None, page=1, threadid=None, theme=None)

        if not web_input.chan:
            raise web.seeother("/")

        render._keywords['globals']['model'] = {"current_thread": web_input.threadid,
                                                "current_page": web_input.page,
                                                "current_chan": web_input.chan}

        return render.base(render.pages.board())

    def POST(self, url):
        web_input = web.input(chan=None, subject="", body="", image=None, theme=None)

        if web_input.theme:
            config.theme = web_input.theme
            raise web.seeother(web.ctx.query)

        render._keywords['globals']['model'] = {"current_chan": web_input.chan}

        if not web_input.chan:
            render._keywords['globals']['model']['status_message'] = "You must post to a valid chan!"
        elif len(web_input.subject.strip()) == 0 or len(web_input.body.strip()) == 0:
            render._keywords['globals']['model']['status_message'] = "You must include a subject and message."

        if "status_message" in render._keywords['globals']['model']:
            render._keywords['globals']['model']['status_title'] = "Uh oh, something went wrong!"
            return render.base(render.pages.alert())

        result = nexus.submitPost(web_input.chan, web_input.subject, web_input.body, web_input.image)
        render._keywords['globals']['model']['status_title'] = "Success"
        render._keywords['globals']['model']['status_message'] = result

        return render.base(render.pages.alert())


class Thread:
    def __init__(self):
        pass

    def GET(self, url):
        web_input = web.input(chan=None, threadid=None, theme=None)

        render._keywords['globals']['model'] = {"current_thread": web_input.threadid,
                                                "current_chan": web_input.chan}

        if not web_input.chan:
            raise web.seeother("/")

        return render.base(render.pages.thread())

    def POST(self, url):
        web_input = web.input(chan=None, subject="", body="", image=None, theme=None)

        if web_input.theme:
            config.theme = web_input.theme
            raise web.seeother(web.ctx.query)

        render._keywords['globals']['model'] = {"current_thread": web_input.threadid,
                                                "current_chan": web_input.chan}

        if not web_input.chan:
            render._keywords['globals']['model']['status_message'] = "You must post to a valid chan!"
        elif len(web_input.subject.strip()) == 0 or len(web_input.body.strip()) == 0:
            render._keywords['globals']['model']['status_message'] = "You must include a subject and message."

        if "status_message" in render._keywords['globals']['model']:
            render._keywords['globals']['model']['status_title'] = "Uh oh, something went wrong!"
            return render.base(render.pages.alert())

        result = nexus.submitPost(web_input.chan, web_input.subject, web_input.body, web_input.image)
        render._keywords['globals']['model']['status_title'] = "Success"
        render._keywords['globals']['model']['status_message'] = result

        return render.base(render.pages.alert())


class Index:
    def __init__(self):
        pass

    def POST(self, url):
        web_input = web.input(theme=None)

        if web_input.theme:
            config.theme = web_input.theme
            raise web.seeother(web.ctx.query)

    def GET(self, url):

        render._keywords['globals']['model'] = {}
        status = nexus.getAPIStatus()

        if not status == True:
            render._keywords['globals']['model']['status_title'] = "Success"
            render._keywords['globals']['model']['status_message'] = status

        return render.base(render.pages.index())


if __name__ == "__main__":
    app.run()
