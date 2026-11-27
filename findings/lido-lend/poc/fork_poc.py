#!/usr/bin/env python3
"""Fork-style eth_call PoCs against the Lido Lend pin. Never submit. Txs via eth_call only."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

from Crypto.Hash import keccak

RPC = "https://eth.drpc.org"
BLOCK = "0x1947bfb"  # 26508283
CORE = "0x026a770badc7126c7252Ef8d407E5b9C56147491"
ADAPTER = "0xb1A64663B5390Ecf1a582df7e19d0a6753d1B84A"
BUNDLER = "0x0056b888E90a1b783311351B54B782dE5de61e87"
VAULT = "0xd8765FA896be3D30A49B9a7d95453E34E2c7A056"
ORACLE = "0x20a078F9940dC05C46De4153D1bCbd54D2b5b151"
WSTETH = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
MORPHO_BOOK = "0xAd28EFa8f2ef56a68b0Eb6836f4aE1d2D6459Ecd"
ERC4626_BOOK = "0x0d2580e4c9b20507eDFAeFC7777d760F12Ad55D4"
MARKET_ID = "e4af8961b4e5a779b85d8c461be1007e4b78a7933976e0a5f23121682020de29"
EOA = "0x000000000000000000000000000000000000dEaD"


def sel(sig: str) -> str:
    h = keccak.new(digest_bits=256)
    h.update(sig.encode())
    return h.hexdigest()[:8]


def pad32(hex_or_int) -> str:
    if isinstance(hex_or_int, int):
        return f"{hex_or_int:064x}"
    s = hex_or_int.lower().replace("0x", "")
    return s.zfill(64)


def addr_word(a: str) -> str:
    return pad32(a.lower().replace("0x", ""))


def rpc(method: str, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(
        RPC,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "curl/8.5.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.loads(resp.read().decode())
    if "error" in out:
        raise RuntimeError(out["error"])
    return out["result"]


def call(to: str, data: str, frm: str | None = None) -> tuple[str | None, str | None]:
    tx = {"to": to, "data": data}
    if frm:
        tx["from"] = frm
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [tx, BLOCK]}
    ).encode()
    req = urllib.request.Request(
        RPC,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "curl/8.5.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return None, f"http {e.code}"
    if "error" in out:
        err = out["error"]
        return None, json.dumps(err)[:300]
    return out.get("result"), None


def u256(word: str) -> int:
    return int(word, 16)


def decode_revert(err: str) -> str:
    # geth: {"message": "execution reverted: ...", "data": "0x..."}
    try:
        obj = json.loads(err)
    except json.JSONDecodeError:
        return err[:200]
    data = ""
    if isinstance(obj, dict):
        data = str(obj.get("data") or "")
        msg = str(obj.get("message") or "")
    else:
        msg = err
    if data.startswith("0x") and len(data) >= 10:
        selector = data[2:10]
        return f"revert selector 0x{selector} data_len={len(data)}"
    return msg[:200]


def market_state():
    data = "0x" + sel("market(bytes32)") + MARKET_ID
    raw, err = call(CORE, data)
    if err:
        return {"error": err}
    r = raw[2:] if raw and raw.startswith("0x") else (raw or "")
    words = [r[i : i + 64] for i in range(0, len(r), 64)]
    names = [
        "totalSupplyAssets",
        "totalSupplyShares",
        "totalBorrowAssets",
        "totalBorrowShares",
        "lastUpdate",
        "fee",
    ]
    return {n: u256(w) for n, w in zip(names, words)}


def lead_001():
    print("=== L-P1-001 fork eth_call @ block", BLOCK, "===")
    mk = market_state()
    print("core.market(proposedId):", json.dumps(mk))

    raw, err = call(CORE, "0x" + sel("isSettlementEnabled(bytes32)") + MARKET_ID)
    print("isSettlementEnabled:", None if err else int(raw, 16), "err", err)

    raw, err = call(VAULT, "0x" + sel("totalSupply()"))
    print("vault.totalSupply:", None if err else int(raw, 16), "err", err)

    raw, err = call(VAULT, "0x" + sel("totalAssets()"))
    print("vault.totalAssets:", None if err else int(raw, 16), "err", err)

    raw, err = call(ORACLE, "0x" + sel("price()"))
    print("oracle.price:", None if err else int(raw, 16), "err", err)

    raw, err = call(WSTETH, "0x" + sel("getStETHByWstETH(uint256)") + pad32(10**36))
    print("wstETH.getStETHByWstETH(1e36):", None if err else int(raw, 16), "err", err)

    # adapter.fallbackExit not via Bundler3
    adapter_data = (
        "0x"
        + sel("fallbackExit(address,uint256,uint256,address,uint256,uint256)")
        + addr_word(VAULT)
        + pad32(10**18)
        + pad32(0)
        + addr_word(EOA)
        + pad32(1)
        + pad32(0)
    )
    raw, err = call(ADAPTER, adapter_data, frm=EOA)
    print("adapter.fallbackExit as EOA:", "ok" if raw else decode_revert(err or ""))

    # vault.fallbackExit as EOA with 1 share
    vault_data = (
        "0x"
        + sel("fallbackExit(uint256,address,address,uint256)")
        + pad32(1)
        + addr_word(EOA)
        + addr_word(EOA)
        + pad32(0)
    )
    raw, err = call(VAULT, vault_data, frm=EOA)
    print("vault.fallbackExit 1 share as EOA:", "ok" if raw else decode_revert(err or ""))

    # rounding bound: toAssetsUp - toAssetsDown <= 1 for any (shares, totals)
    VIRTUAL_SHARES = 10**6
    VIRTUAL_ASSETS = 1

    def to_down(shares, ta, ts):
        return shares * (ta + VIRTUAL_ASSETS) // (ts + VIRTUAL_SHARES)

    def to_up(shares, ta, ts):
        d = ts + VIRTUAL_SHARES
        return (shares * (ta + VIRTUAL_ASSETS) + d - 1) // d

    max_gap = 0
    for ta, ts, sh in (
        (0, 0, 1),
        (1, 10**6, 1),
        (10**18, 10**18, 1),
        (10**18, 10**24, 10**18),
        (2 * 10**18 - 1, 10**18, 3),
        (10**27, 7, 1),
    ):
        g = to_up(sh, ta, ts) - to_down(sh, ta, ts)
        max_gap = max(max_gap, g)
    print("toAssetsUp-toAssetsDown samples max:", max_gap, "(Morpho mulDiv gap is 0 or 1)")

    price = 12 * 10**35  # ~1.2e36 if live oracle failed
    if not err:
        pass
    raw_p, err_p = call(ORACLE, "0x" + sel("price()"))
    if not err_p and raw_p:
        price = int(raw_p, 16)
    SCALE = 10**36
    # inverse mulDiv truncation for seized = down * SCALE / price; value = seized * price / SCALE
    down = 10**18
    seized = down * SCALE // price if price else 0
    value = seized * price // SCALE if price else 0
    print("oracle mulDiv inverse gap at 1e18 down:", down - value, "price", price)

    print("LIVE_SETTLE_PATH:", mk.get("lastUpdate", 0) != 0)
    print("DONE L-P1-001")


ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
CONTROLLER = "0xCF1B266d320CA9c0d4e13eF2C46465962F040e88"
GUARDIAN = "0xc8a8CBBF4c55980F85332fD8470DF0fC52d690aC"
IRM = "0x81B7cC9523B30429110282d90db2fa90ff443d91"
OWNER_FACADE = "0x85378a1073E8f338e11A97E090E47e2F0FdD3D5a"
BREAKER = "0xd0A81A130a303237d338A0b5835edcB011Ab3afd"
FACTORY = "0xBe1C1eaBda3eD8a93D3CE3246cf4EeF8111c76C7"
PRESEEDER = "0x3F107d1fbCA49F425321Cb27f6Ef5CbB94a72c41"
ACTIVATE = "0x17bb2A2B5983D29392A5d31D627D4C8B13383fe6"
CORE_IMPL = "0xa40Bd2281F54A2D3845F9535b74D2abD946E1911"
IRM_IMPL = "0x683eA34c29658fb6cDeCc92Eb4B4e7f766979868"


def storage(addr: str, slot: str) -> str:
    return rpc("eth_getStorageAt", [addr, slot, BLOCK])


def word_addr(word: str) -> str:
    w = word.lower().replace("0x", "").zfill(64)
    return "0x" + w[24:]


def lead_003():
    print("=== PASS-3 fork reads @ block", BLOCK, "===")
    for name, addr in (
        ("LidoLend proxy", CORE),
        ("IrmRouter proxy", IRM),
        ("controller proxy", CONTROLLER),
        ("vault proxy", VAULT),
        ("guardian proxy", GUARDIAN),
        ("oracle proxy", ORACLE),
    ):
        try:
            admin = word_addr(storage(addr, ADMIN_SLOT))
            impl = word_addr(storage(addr, IMPL_SLOT))
            print(f"{name} admin={admin} impl={impl}")
        except Exception as e:
            print(f"{name} storage err {e}")

    raw, err = call(CORE, "0x" + sel("owner()"))
    print("core.owner:", word_addr(raw) if raw else err)
    raw, err = call(CORE, "0x" + sel("isInitialized()"))
    print("core.isInitialized:", None if err else bool(int(raw, 16)), "err", err)

    raw, err = call(IRM, "0x" + sel("isInitialized()"))
    print("irmRouter.isInitialized:", None if err else bool(int(raw, 16)), "err", err)
    raw, err = call(IRM, "0x" + sel("owner()"))
    print("irmRouter.owner:", word_addr(raw) if raw else err)

    raw, err = call(CONTROLLER, "0x" + sel("marketId()"))
    print("controller.marketId:", raw if raw else err)
    raw, err = call(CONTROLLER, "0x" + sel("isFrozen()"))
    print("controller.isFrozen:", None if err else bool(int(raw, 16)), "err", err)
    raw, err = call(CONTROLLER, "0x" + sel("guardianSignals()"))
    print("controller.guardianSignals:", word_addr(raw) if raw else err)
    raw, err = call(CONTROLLER, "0x" + sel("paused()"))
    print("controller.paused:", raw if raw else err)

    raw, err = call(VAULT, "0x" + sel("asset()"))
    print("vault.asset:", word_addr(raw) if raw else err)
    raw, err = call(VAULT, "0x" + sel("marketId()"))
    print("vault.marketId:", raw if raw else err)
    raw, err = call(VAULT, "0x" + sel("controller()"))
    print("vault.controller:", word_addr(raw) if raw else err)

    # unprivileged initialize on live proxies
    init_core = "0x" + sel("initialize(address)") + addr_word(EOA)
    raw, err = call(CORE, init_core, frm=EOA)
    print("core.initialize(eoa):", "ok" if raw else decode_revert(err or ""))
    raw, err = call(CORE_IMPL, init_core, frm=EOA)
    print("coreImpl.initialize(eoa):", "ok" if raw else decode_revert(err or ""))

    init_irm = "0x" + sel("initialize(address,address)") + addr_word(EOA) + addr_word(EOA)
    raw, err = call(IRM, init_irm, frm=EOA)
    print("irmRouter.initialize(eoa,eoa):", "ok" if raw else decode_revert(err or ""))

    # unprivileged createMarket
    # skip full MarketParams encode; owner-only should fail even with zeros
    raw, err = call(CORE, "0x" + sel("createMarket((address,address,address,address,uint256))") + "00" * 160, frm=EOA)
    print("core.createMarket zeros as EOA:", "ok" if raw else decode_revert(err or ""))

    raw, err = call(OWNER_FACADE, "0x" + sel("owner()"))
    print("LidoLendOwner.owner:", word_addr(raw) if raw else err)

    for sig in (
        "owner()",
        "pauseDuration()",
        "heartbeatInterval()",
        "DEFAULT_ADMIN_ROLE()",
        "isPaused(address)",
    ):
        data = "0x" + sel(sig)
        if "address" in sig:
            data += addr_word(CONTROLLER)
        raw, err = call(BREAKER, data)
        print(f"breaker.{sig}:", (raw[:66] if raw else None), "err", err)

    # factory is permissionless: just confirm code and ADMIN immutable if present
    raw, err = call(FACTORY, "0x" + sel("ADMIN()"))
    print("factory.ADMIN:", word_addr(raw) if raw else err)
    raw, err = call(PRESEEDER, "0x" + sel("lidoLend()"))
    print("preseeder.lidoLend:", word_addr(raw) if raw else err)

    print("DONE PASS-3")


def lead_002():
    print("=== L-P1-002 fork eth_call @ block", BLOCK, "===")
    for name, book in (("MorphoExitBook", MORPHO_BOOK), ("Erc4626ExitBook", ERC4626_BOOK)):
        raw, err = call(book, "0x" + sel("lastRequestId()"))
        print(f"{name}.lastRequestId:", None if err else int(raw, 16), "err", err)
        raw, err = call(book, "0x" + sel("paused()"))
        print(f"{name}.paused:", None if err else bool(int(raw, 16)), "err", err)

    raw, err = call(MORPHO_BOOK, "0x" + sel("isMarketAllowed(bytes32)") + MARKET_ID)
    print("MorphoExitBook.isMarketAllowed(proposedId):", None if err else bool(int(raw, 16)), "err", err)

    fill = (
        "0x"
        + sel("fillExitRequest(uint256,uint256,address)")
        + pad32(1)
        + pad32(10**18)
        + addr_word(EOA)
    )
    for name, book in (("MorphoExitBook", MORPHO_BOOK), ("Erc4626ExitBook", ERC4626_BOOK)):
        raw, err = call(book, fill, frm=EOA)
        print(f"{name}.fillExitRequest(1, 1e18, dead):", "ok" if raw else decode_revert(err or ""))

    print("DONE L-P1-002")


WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
GENERAL = "0x0C6151F0205A6Edf143b42C4f7B4E97a8f099260"
AGENT = "0x3e40d73eb977dc6a537af587d48316fee66e9c8c"
LLTV = 980000000000000000
ORACLE_ADDR = ORACLE
IRM_ADDR = IRM if "IRM" in dir() else "0x81B7cC9523B30429110282d90db2fa90ff443d91"


def role_id(name: str) -> str:
    return keccak.new(digest_bits=256).update(name.encode()).hexdigest()


def market_params_words() -> str:
    return (
        addr_word(WETH)
        + addr_word(WSTETH)
        + addr_word(ORACLE)
        + addr_word("0x81B7cC9523B30429110282d90db2fa90ff443d91")
        + pad32(LLTV)
    )


def encode_bytes_tail(head_words: int, payload_hex: str = "") -> str:
    offset = head_words * 32
    n = len(payload_hex) // 2
    return pad32(offset) + pad32(n) + payload_hex


def lead_006():
    print("=== PASS-6 fork eth_call @ block", BLOCK, "===")
    raw, err = call(VAULT, "0x" + sel("managedSupplyShares()"))
    print("vault.managedSupplyShares:", None if err else int(raw, 16), "err", err)
    raw, err = call(VAULT, "0x" + sel("totalSupply()"))
    print("vault.totalSupply:", None if err else int(raw, 16), "err", err)
    raw, err = call(VAULT, "0x" + sel("totalAssets()"))
    print("vault.totalAssets:", None if err else int(raw, 16), "err", err)
    raw, err = call(CONTROLLER, "0x" + sel("maxDeposit()"))
    print("controller.maxDeposit:", None if err else int(raw, 16), "err", err)
    raw, err = call(CONTROLLER, "0x" + sel("supplyCap()"))
    print("controller.supplyCap:", None if err else int(raw, 16), "err", err)
    raw, err = call(CONTROLLER, "0x" + sel("isPaused()"))
    print("controller.isPaused:", None if err else bool(int(raw, 16)), "err", err)
    raw, err = call(CONTROLLER, "0x" + sel("isFrozen()"))
    print("controller.isFrozen:", None if err else bool(int(raw, 16)), "err", err)
    raw, err = call(CONTROLLER, "0x" + sel("settlementBorrowersCount()"))
    print("controller.settlementBorrowersCount:", None if err else int(raw, 16), "err", err)

    inst = []
    for who, label in ((EOA, "eoa"), (BUNDLER, "bundler"), (ADAPTER, "vaultAdapter"), (GENERAL, "genAdapter")):
        raw, err = call(CONTROLLER, "0x" + sel("hasInstantActivation(address)") + addr_word(who))
        inst.append(f"{label}={None if err else bool(int(raw, 16))}")
    print("instantActivation:", " ".join(inst))

    admin_role = "0" * 64
    for role_name, role in (
        ("DEFAULT_ADMIN_ROLE", admin_role),
        ("PAUSER_ROLE", role_id("PAUSER_ROLE")),
        ("FREEZER_ROLE", role_id("FREEZER_ROLE")),
        ("RESUMER_ROLE", role_id("RESUMER_ROLE")),
        ("MANAGER_ROLE", role_id("MANAGER_ROLE")),
        ("UNFREEZER_ROLE", role_id("UNFREEZER_ROLE")),
    ):
        bits = []
        for who, label in ((AGENT, "agent"), (BREAKER, "cb"), (EOA, "eoa")):
            raw, err = call(
                CONTROLLER, "0x" + sel("hasRole(bytes32,address)") + role + addr_word(who)
            )
            bits.append(f"{label}={None if err else bool(int(raw, 16))}")
        print(f"hasRole.{role_name}:", " ".join(bits))

    raw, err = call(CONTROLLER, "0x" + sel("pauseFor(uint256)") + pad32(1), frm=EOA)
    print("controller.pauseFor(1) eoa:", "ok" if raw else decode_revert(err or ""))
    raw, err = call(CONTROLLER, "0x" + sel("freeze()"), frm=EOA)
    print("controller.freeze eoa:", "ok" if raw else decode_revert(err or ""))
    raw, err = call(
        CONTROLLER,
        "0x" + sel("setInstantActivation(address,bool)") + addr_word(EOA) + pad32(1),
        frm=EOA,
    )
    print("controller.setInstantActivation eoa:", "ok" if raw else decode_revert(err or ""))

    on_data = (
        "0x"
        + sel("on(bytes32,uint8,bytes)")
        + MARKET_ID
        + pad32(0)
        + encode_bytes_tail(3)
    )
    raw, err = call(CONTROLLER, on_data, frm=EOA)
    print("controller.on Supply eoa:", "ok" if raw else decode_revert(err or ""))

    dep = "0x" + sel("deposit(uint256,address)") + pad32(1) + addr_word(EOA)
    raw, err = call(VAULT, dep, frm=EOA)
    print("vault.deposit(1) eoa:", "ok" if raw else decode_revert(err or ""))

    params = market_params_words()
    supply = (
        "0x"
        + sel("supply((address,address,address,address,uint256),uint256,uint256,address,bytes)")
        + params
        + pad32(1)
        + pad32(0)
        + addr_word(EOA)
        + encode_bytes_tail(9)
    )
    raw, err = call(CORE, supply, frm=EOA)
    print("core.supply 1 wei published:", "ok" if raw else decode_revert(err or ""))

    borrow = (
        "0x"
        + sel("borrow((address,address,address,address,uint256),uint256,uint256,address,address)")
        + params
        + pad32(1)
        + pad32(0)
        + addr_word(EOA)
        + addr_word(EOA)
    )
    raw, err = call(CORE, borrow, frm=EOA)
    print("core.borrow 1 wei published:", "ok" if raw else decode_revert(err or ""))

    coll = (
        "0x"
        + sel("supplyCollateral((address,address,address,address,uint256),uint256,address,bytes)")
        + params
        + pad32(1)
        + addr_word(EOA)
        + encode_bytes_tail(8)
    )
    raw, err = call(CORE, coll, frm=EOA)
    print("core.supplyCollateral 1 wei:", "ok" if raw else decode_revert(err or ""))

    raw, err = call(CONTROLLER, "0x" + sel("setSettlementLtv(uint256)") + pad32(10**17), frm=EOA)
    print("controller.setSettlementLtv(0.1e18) eoa:", "ok" if raw else decode_revert(err or ""))

    raw, err = call(ORACLE, "0x" + sel("WSTETH()"))
    print("oracle.WSTETH:", word_addr(raw) if raw else err)
    raw, err = call(ORACLE, "0x" + sel("price()"))
    print("oracle.price:", None if err else int(raw, 16), "err", err)
    raw, err = call(WSTETH, "0x" + sel("getStETHByWstETH(uint256)") + pad32(10**36))
    print("wstETH.getStETHByWstETH(1e36):", None if err else int(raw, 16), "err", err)

    for token, tname in ((WETH, "WETH"), (WSTETH, "wstETH")):
        for who, wname in (
            (VAULT, "vault"),
            (ADAPTER, "vaultAdapter"),
            (GENERAL, "genAdapter"),
            (BUNDLER, "bundler"),
            (CORE, "core"),
        ):
            raw, err = call(token, "0x" + sel("balanceOf(address)") + addr_word(who))
            bal = None if err else int(raw, 16)
            if bal:
                print(f"{tname}.balanceOf.{wname}:", bal)

    imms = []
    for sig in ("BUNDLER3()", "MORPHO()", "WRAPPED_NATIVE()", "ST_ETH()", "WST_ETH()"):
        raw, err = call(GENERAL, "0x" + sel(sig))
        imms.append(f"{sig}={word_addr(raw) if raw else decode_revert(err or '')}")
    print("genAdapter:", " ".join(imms))

    raw, err = call(ADAPTER, "0x" + sel("BUNDLER3()"))
    print("vaultAdapter.BUNDLER3:", word_addr(raw) if raw else decode_revert(err or ""))

    raw, err = call(BUNDLER, "0x" + sel("initiator()"))
    print("bundler.initiator idle:", word_addr(raw) if raw else decode_revert(err or ""))

    adapter_from_bundler = (
        "0x"
        + sel("fallbackExit(address,uint256,uint256,address,uint256,uint256)")
        + addr_word(VAULT)
        + pad32(1)
        + pad32(0)
        + addr_word(EOA)
        + pad32(0)
        + pad32(0)
    )
    raw, err = call(ADAPTER, adapter_from_bundler, frm=BUNDLER)
    print("adapter.fallbackExit from Bundler3 idle:", "ok" if raw else decode_revert(err or ""))

    raw, err = call(
        GENERAL,
        "0x" + sel("erc20Transfer(address,address,uint256)") + addr_word(WETH) + addr_word(EOA) + pad32(1),
        frm=EOA,
    )
    print("genAdapter.erc20Transfer eoa:", "ok" if raw else decode_revert(err or ""))

    # empty multicall
    mc = "0x" + sel("multicall((address,bytes,uint256,bool,bytes32)[])") + pad32(32) + pad32(0)
    raw, err = call(BUNDLER, mc, frm=EOA)
    print("bundler.multicall [] eoa:", "ok" if raw else decode_revert(err or ""))
    print("DONE PASS-6")


def main():
    lead = sys.argv[1] if len(sys.argv) > 1 else "all"
    if lead in ("001", "all"):
        lead_001()
    if lead in ("002", "all"):
        lead_002()
    if lead in ("003", "pass3", "all"):
        lead_003()
    if lead in ("006", "pass6"):
        lead_006()


if __name__ == "__main__":
    main()
