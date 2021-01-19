import './App.css';
import React from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import ListGroup from "react-bootstrap/ListGroup";


class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isLoaded: false,
            items: {},
            error: null
        };
    }

    getRealtimeData(e) {
        e = JSON.parse(e);
        let key = e.service + '/' + e.color;
        this.state.items[key] = e
        this.setState(state => ({
            items: this.state.items
        }))

    }

    componentWillUnmount() {
        this.state.sseObj.close()
    }

    componentDidMount() {
        fetch("/components",
            {
                credentials: 'include'
            })
            .then(res => res.json())
            .then(
                (result) => {
                    var item_dict = {};
                    result.forEach(el => item_dict[el.service + '/' + el.color] = el);
                    this.setState({
                        isLoaded: true,
                        items: item_dict
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            );
        const sse = new EventSource('/stream', {withCredentials: true});
        sse.onmessage = e => this.getRealtimeData(e.data);
        sse.onerror = () => {
            // error log here
            sse.close();
        }
        this.setState({
            sseObj: sse
        });

    }


    render() {
        const {error, isLoaded, items} = this.state;
        if (error) {
            return <div>Error Loading Components: {error.message}</div>;
        } else if (!isLoaded) {
            return <div>Loading...</div>;
        } else {
            var vals = []
            Object.keys(items).forEach(k => vals.push(items[k]));

            return (
                <Container fluid>
                    <Row>
                        <Col>
                            <ListGroup>
                                {vals.filter(item => item.color === "blue")
                                    .map(item => (
                                        <ListGroup.Item
                                            key={item.service + '/' + item.color}
                                            variant={item.state === 0 ? 'danger' : 'success'}
                                            >
                                            {item.service}/{item.color} {item.state}
                                        </ListGroup.Item>

                                    ))}
                            </ListGroup>
                        </Col>
                        <Col>
                            <ListGroup>
                                {vals.filter(item => item.color === "green")
                                    .map(item => (
                                        <ListGroup.Item
                                            key={item.service + '/' + item.color}
                                            variant={item.state === 0 ? 'danger' : 'success'}>
                                            {item.service}/{item.color} {item.state}
                                        </ListGroup.Item>
                                    ))}
                            </ListGroup>
                        </Col>
                    </Row>
                    <Row className='mt-3'>
                        <Col>
                            <ListGroup>
                                {vals.filter(item => item.service === "floodlight")
                                    .map(item => (
                                        <ListGroup.Item
                                            key={item.service + '/' + item.color}
                                            variant={item.state === 0 ? 'danger' : 'success'}
                                            >
                                            {item.service}/{item.color} {item.state}
                                        </ListGroup.Item>

                                    ))}
                            </ListGroup>
                        </Col>
                        <Col>
                            <ListGroup>
                                {vals.filter(item => item.color !== "green" && item.color !== "blue" && item.service !== "floodlight")
                                    .map(item => (
                                        <ListGroup.Item
                                            key={item.service + '/' + item.color}
                                            variant={item.state === 0 ? 'danger' : 'success'}>
                                            {item.service}/{item.color} {item.state}
                                        </ListGroup.Item>
                                    ))}
                            </ListGroup>
                        </Col>
                    </Row>
                </Container>);
        }
    }

}

export default App;
