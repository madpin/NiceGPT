#!/usr/bin/env python3
"""This is just a very simple authentication example.

Please see the `OAuth2 example at FastAPI <https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/>`_  or
use the great `Authlib package <https://docs.authlib.org/en/v0.13/client/starlette.html#using-fastapi>`_ to implement a classing real authentication system.
Here we just demonstrate the NiceGUI integration.
"""
from fastapi.responses import RedirectResponse
from typing import List, Tuple

from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI

from nicegui import app, ui, Client
from dotenv import load_dotenv, find_dotenv
import os

# in reality users passwords would obviously need to be hashed
passwords = {"m": "p", "user2": "pass2"}

_ = load_dotenv(find_dotenv())  # read local .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "not-set")

llm = ConversationChain(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)
)

messages: List[Tuple[str, str, str]] = []
thinking: bool = False

@ui.refreshable
async def chat_messages() -> None:
    for name, text in messages:
        ui.chat_message(text=text, name=name, sent=name == "You")
    if thinking:
        ui.spinner(size="3rem").classes("self-center")
    await ui.run_javascript(
        "window.scrollTo(0, document.body.scrollHeight)", respond=False
    )

@ui.page("/")
def main_page() -> None:
    if not app.storage.user.get("authenticated", False):
        return RedirectResponse("/login")
    with ui.column().classes("absolute-center items-center"):
        ui.label(f'Hello {app.storage.user["username"]}!').classes("text-2xl")
        ui.button(
            # on_click=lambda: (app.storage.user.clear(), ui.open("/login"))
            on_click=lambda: ui.open('/page_layout')
        ).props("outline round icon=logout")


@ui.page("/login")
def login() -> None:
    def try_login() -> (
        None
    ):  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update({"username": username.value, "authenticated": True})
            ui.open("/")
        else:
            ui.notify("Wrong username or password", color="negative")

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/")
    with ui.card().classes("absolute-center"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = (
            ui.input("Password").on("keydown.enter", try_login).props("type=password")
        )
        ui.button("Log in", on_click=try_login)


@ui.page("/page_layout")
async def page_layout(client: Client):
    if not app.storage.user.get("authenticated", False):
        return RedirectResponse("/login")

    with ui.header(elevated=True).style("background-color: #3874c8").classes(
        "items-center justify-between"
    ):
        ui.button(on_click=lambda: left_drawer.toggle()).props(
            "flat color=white icon=menu"
        )
        ui.label("HEADER")
        ui.button(on_click=lambda: right_drawer.toggle()).props(
            "flat color=white icon=menu"
        )
    with ui.left_drawer(fixed=False).style("background-color: #ebf1fa").props(
        "bordered"
    ) as left_drawer:
        ui.label("LEFT DRAWER")
    with ui.right_drawer(fixed=False).style("background-color: #ebf1fa").props(
        "bordered"
    ) as right_drawer:
        ui.label("RIGHT DRAWER")
    with ui.footer().style("background-color: #3874c8"):
        ui.label("FOOTER")

    async def send() -> None:
        global thinking
        message = text.value
        messages.append(("You", text.value))
        thinking = True
        text.value = ""
        chat_messages.refresh()

        response = await llm.arun(message)
        messages.append(("Bot", response))
        thinking = False
        chat_messages.refresh()

    anchor_style = r"a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}"
    ui.add_head_html(f"<style>{anchor_style}</style>")
    await client.connected()

    with ui.column().classes("w-full max-w-2xl mx-auto items-stretch"):
        await chat_messages()

    with ui.footer().classes("bg-white"), ui.column().classes(
        "w-full max-w-3xl mx-auto my-6"
    ):
        with ui.row().classes("w-full no-wrap items-center"):
            placeholder = (
                "message"
                if OPENAI_API_KEY != "not-set"
                else "Please provide your OPENAI key in the Python script first!"
            )
            text = (
                ui.input(placeholder=placeholder)
                .props("rounded outlined input-class=mx-3")
                .classes("w-full self-center")
                .on("keydown.enter", send)
            )
        ui.markdown("simple chat app built with [NiceGUI](https://nicegui.io)").classes(
            "text-xs self-end mr-8 m-[-1em] text-primary"
        )

ui.run(storage_secret="THIS_NEEDS_TO_BE_CHANGED", port=8097)
