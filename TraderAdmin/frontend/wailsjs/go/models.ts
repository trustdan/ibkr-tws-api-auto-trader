export namespace main {
	
	export class Position {
	    symbol: string;
	    quantity: number;
	    avgPrice: number;
	    unrealizedPnL: number;
	
	    static createFrom(source: any = {}) {
	        return new Position(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.symbol = source["symbol"];
	        this.quantity = source["quantity"];
	        this.avgPrice = source["avgPrice"];
	        this.unrealizedPnL = source["unrealizedPnL"];
	    }
	}
	export class Signal {
	    symbol: string;
	    signal: number;
	    timestamp: number;
	
	    static createFrom(source: any = {}) {
	        return new Signal(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.symbol = source["symbol"];
	        this.signal = source["signal"];
	        this.timestamp = source["timestamp"];
	    }
	}

}

