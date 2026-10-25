-- Pure Lua decision helper. No SCAR, audio, RNG or UI calls.
-- The caller must qualify/filter its event sensor before record().
local Policy = {}

local function finite(n)
    return type(n) == 'number' and n == n and n > -math.huge and n < math.huge
end

function Policy.classify(rate)
    assert(finite(rate) and rate >= 0, 'rate must be finite and nonnegative')
    if rate == 0 then return 'exploration' end
    if rate < 8 then return 'small' end
    if rate <= 24 then return 'medium' end
    return 'large'
end

function Policy.percent(value)
    if not finite(value) then return 3 end
    return math.max(0, math.min(100, value))
end

function Policy.new(start, interval, window)
    start, interval, window = start or 0, interval or 15, window or 1
    assert(finite(start), 'start must be finite')
    assert(finite(interval) and interval > 0, 'interval must be positive')
    assert(finite(window) and window > 0, 'window must be positive')
    local self = {start = start, last_clock = start, interval = interval, window = window,
                  next_boundary = start + interval, state = 'exploration', events = {}}

    function self.record(now, eligible)
        if eligible ~= true then return false end
        assert(finite(now) and now >= self.start, 'invalid event time')
        self.events[#self.events + 1] = now
        return true
    end

    function self.tick(now)
        assert(finite(now) and now >= self.last_clock, 'invalid clock; reset on restore')
        self.last_clock = now
        -- Prune even on heartbeat ticks, retaining at most the active window.
        -- (now-window, now] is the defined rate window.
        local kept, count = {}, 0
        for _, t in ipairs(self.events) do
            if t > now - self.window then
                kept[#kept + 1] = t
                if t <= now then count = count + 1 end
            end
        end
        self.events = kept
        if now < self.next_boundary then return nil end
        -- Advance from the original phase, never now + interval; a late tick
        -- emits one decision, not a burst of past transitions.
        local slot = math.floor((now - self.start) / self.interval)
        self.next_boundary = self.start + (slot + 1) * self.interval
        local rate = count / self.window
        local state = Policy.classify(rate)
        local changed = state ~= self.state
        self.state = state
        return {state = state, changed = changed, rate = rate, slot = slot,
                next_boundary = self.next_boundary}
    end

    return self
end

return Policy
