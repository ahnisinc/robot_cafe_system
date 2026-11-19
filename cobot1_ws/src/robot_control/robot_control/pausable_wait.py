def wait_unless_paused(done, is_paused, timeout, tick=0.5):
    """
    done(threading.Event)이 set될 때까지 기다린다.
    is_paused()가 True인 동안의 시간은 timeout에 포함하지 않는다.
    완료되면 True, 타임아웃이면 False.
    """

    elapsed = 0.0

    while not done.wait(tick):
        if not is_paused():
            elapsed += tick

        if elapsed >= timeout:
            return False

    return True
