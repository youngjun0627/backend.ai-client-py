from unittest import mock

import aiohttp
import asynctest
import pytest

from sorna.asyncio.kernel import (
    create_kernel, destroy_kernel, restart_kernel, get_kernel_info,
    execute_code, stream_pty, StreamPty
)
from sorna.exceptions import SornaAPIError
from sorna.request import Request


@pytest.mark.asyncio
async def test_create_kernel_url():
    mock_resp = asynctest.MagicMock(spec=aiohttp.ClientResponse)
    mock_resp.status = 201
    mock_resp.json = asynctest.MagicMock()

    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = mock_resp

    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        await create_kernel('python')

        mock_req_cls.assert_called_once_with('POST', '/kernel/create', mock.ANY)
        mock_req_obj.sign.assert_called_once_with()
        mock_req_obj.asend.assert_called_once_with()
        mock_req_obj.asend.return_value.json.assert_called_once_with()


@pytest.mark.asyncio
async def test_create_kernel_return_id_only():
    mock_resp = asynctest.MagicMock(spec=aiohttp.ClientResponse)
    mock_resp.status = 201
    mock_resp.json = lambda: {'kernelId': 'mock_kernel_id'}

    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = mock_resp

    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        resp = await create_kernel('python')

        assert resp == mock_resp.json()['kernelId']


@pytest.mark.asyncio
async def test_create_kernel_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=400)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj):
        with pytest.raises(SornaAPIError):
            await create_kernel('python')


@pytest.mark.asyncio
async def test_destroy_kernel_url():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=204)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        await destroy_kernel('mykernel')
        mock_req_cls.assert_called_once_with('DELETE', '/kernel/{}'.format('mykernel'))


@pytest.mark.asyncio
async def test_destroy_kernel_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=400)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj):
        with pytest.raises(SornaAPIError):
            await destroy_kernel('mykernel')


@pytest.mark.asyncio
async def test_restart_kernel_url():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=204)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        await restart_kernel('mykernel')
        mock_req_cls.assert_called_once_with('PATCH', '/kernel/{}'.format('mykernel'))


@pytest.mark.asyncio
async def test_restart_kernel_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=400)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj):
        with pytest.raises(SornaAPIError):
            await restart_kernel('mykernel')


@pytest.mark.asyncio
async def test_get_kernel_info_url():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=200)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        await get_kernel_info('mykernel')
        mock_req_cls.assert_called_once_with('GET', '/kernel/{}'.format('mykernel'))


@pytest.mark.asyncio
async def test_get_kernel_info_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=400)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj):
        with pytest.raises(SornaAPIError):
            await get_kernel_info('mykernel')


@pytest.mark.asyncio
async def test_execute_code_url():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=200)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        await execute_code('mykernel', 2, 'hello')
        mock_req_cls.assert_called_once_with('POST', '/kernel/{}'.format('mykernel'),
                                         {'codeId': 2, 'code': 'hello'})


@pytest.mark.asyncio
async def test_execute_code_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.asend.return_value = asynctest.MagicMock(status=400)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        with pytest.raises(SornaAPIError):
            await execute_code('mykernel', 2, 'hello')


@pytest.mark.asyncio
async def test_stream_pty(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    sess, ws = object(), object()
    mock_req_obj.connect_websocket.return_value = (sess, ws)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        stream = await stream_pty('mykernel')
        mock_req_cls.assert_called_once_with('GET', '/stream/kernel/{}/pty'.format('mykernel'))
        mock_req_obj.sign.assert_called_once_with()
        mock_req_obj.connect_websocket.assert_called_once_with()
        assert isinstance(stream, StreamPty)
        assert stream.sess is sess
        assert stream.ws is ws


@pytest.mark.asyncio
async def test_stream_pty_raises_error_with_abnormal_status(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_exception = aiohttp.errors.HttpProcessingError(code=400, message='emulated-handshake-error')
    mock_req_obj.connect_websocket = asynctest.MagicMock(side_effect=mock_exception)
    with asynctest.patch('sorna.asyncio.kernel.Request',
                         return_value=mock_req_obj) as mock_req_cls:
        with pytest.raises(SornaAPIError):
            await stream_pty('mykernel')
        mock_req_obj.sign.assert_called_once_with()
