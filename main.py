import logging
import uuid

import asyncio
import rx
from rx.subject import Subject
from rx.scheduler.eventloop import AsyncIOScheduler

import cozmo

import programs


def run(main, drivers, **kwargs):
    scheduler = kwargs["scheduler"]

    proxies = {}
    for name in drivers:
        proxies[name] = Subject()
    sinks = main(proxies)
    sources = {}
    for name in drivers:
        sources[name] = drivers[name](sinks[name])
        sources[name].subscribe(proxies[name], scheduler=scheduler)


def make_cozmo_driver(**kwargs):
    scheduler = kwargs["scheduler"]
    robot = scheduler._loop.run_until_complete(
        cozmo.connect_on_loop(scheduler._loop).wait_for_robot()
    )

    def cozmo_driver(sink):
        def subscribe(observer, scheduler=None):
            action_handlers = {}

            def on_next(command):
                if "type" not in command or command["type"] == "start":
                    factory = getattr(robot, command["name"])
                    if type(command["value"]) is dict:
                        if "in_parallel" in command["value"]:
                            logging.warning(
                                'Overwriting "in_parallel" field to "True"')
                            command["value"]["in_parallel"] = True
                        command["value"]["in_parallel"] = True
                        action_handlers[command["name"]] = factory(
                            **command["value"])
                    elif type(command["value"]) is list:
                        action_handlers[command["name"]] = factory(
                            **command["value"], in_parallel=True)
                    else:
                        action_handlers[command["name"]] = factory(
                            command["value"], in_parallel=True)

                    if "id" in command:
                        action_handlers[command["name"]].id = command["id"]
                    else:
                        action_handlers[command["name"]].id = str(uuid.uuid4())

                    def on_complete_cb(evt, **kwargs):
                        observer.on_next(
                            dict({
                                "id": action_handlers[command["name"]].id,
                                "evt": evt
                            }, **kwargs))
                    action_handlers[command["name"]].add_event_handler(
                        cozmo.action.EvtActionCompleted,
                        on_complete_cb
                    )
                elif command["type"] == "abort":
                    if action_handlers[command["name"]].is_running:
                        if "id" in command and "id" in action_handlers and command["id"] is not action_handlers["id"]:
                            logging.warning(
                                f'Action id does not match {action_handlers["id"]} {command["id"]}')
                            return
                        action_handlers[command["name"]].abort()
                    else:
                        logging.warning(
                            f'Action {command["name"]} is not running')
                else:
                    logging.warning('Unknown command["type"]', command["type"])

            sink.subscribe(on_next=on_next, scheduler=scheduler)
        source = rx.create(subscribe)
        return source

    return cozmo_driver


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(loop=loop)

    drivers = {
        "Cozmo": make_cozmo_driver(scheduler=scheduler)
    }

    run(programs.main, drivers, scheduler=scheduler)

    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        pass
    finally:
        loop.close()
